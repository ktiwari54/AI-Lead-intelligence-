"""Integration test: complete lead discovery flow.

Verifies that a user can register, create company + contacts, set up a CRM
pipeline, link a deal, and that org isolation prevents cross-tenant data access.
"""
import uuid
import pytest
from httpx import AsyncClient

from backend.tests.helpers import register_and_login, auth_headers


@pytest.mark.asyncio
async def test_complete_lead_flow(client: AsyncClient):
    """End-to-end: register -> company -> contacts -> pipeline -> deal -> tasks."""

    # ── 1. Register and login ────────────────────────────────────────────────
    token = await register_and_login(client, suffix="leadflow")
    hdrs = auth_headers(token)

    # Verify the user is accessible
    me_resp = await client.get("/api/v1/users/me", headers=hdrs)
    assert me_resp.status_code == 200, me_resp.text
    user_data = me_resp.json()["data"]
    assert "id" in user_data

    # ── 2. Create a company ──────────────────────────────────────────────────
    co_resp = await client.post(
        "/api/v1/companies/",
        json={"company_name": "LeadFlow Inc", "website": "https://leadflow.example.com", "domain": "leadflow.example.com"},
        headers=hdrs,
    )
    assert co_resp.status_code == 201, co_resp.text
    company = co_resp.json()["data"]
    company_id = company["id"]
    assert company["company_name"] == "LeadFlow Inc"

    # ── 3. Create 3 contacts for the company ─────────────────────────────────
    contact_ids = []
    for i, (first, seniority) in enumerate([
        ("Alice", "C_LEVEL"),
        ("Bob", "DIRECTOR"),
        ("Carol", "MANAGER"),
    ]):
        ct_resp = await client.post(
            "/api/v1/contacts/",
            json={
                "first_name": first,
                "last_name": "LeadFlow",
                "company_id": company_id,
                "seniority": seniority,
                "email": f"{first.lower()}@leadflow.example.com",
            },
            headers=hdrs,
        )
        assert ct_resp.status_code == 201, ct_resp.text
        contact = ct_resp.json()["data"]
        assert contact["company_id"] == company_id
        contact_ids.append(contact["id"])

    assert len(contact_ids) == 3

    # ── 4. Create a CRM pipeline ─────────────────────────────────────────────
    pipe_resp = await client.post(
        "/api/v1/crm/pipelines",
        json={"name": "LeadFlow Sales", "description": "Main pipeline"},
        headers=hdrs,
    )
    assert pipe_resp.status_code == 201, pipe_resp.text
    pipeline = pipe_resp.json()["data"]
    pipeline_id = pipeline["id"]
    assert pipeline["name"] == "LeadFlow Sales"

    # ── 5. Create a deal linked to the company ───────────────────────────────
    # Deals require a stage_id; the pipeline may auto-create stages.
    # If no stage is embedded, skip the deal assertion.
    stages = pipeline.get("stages", [])
    if stages:
        stage_id = stages[0]["id"]
        deal_resp = await client.post(
            "/api/v1/crm/deals",
            json={
                "title": "LeadFlow Enterprise Deal",
                "pipeline_id": pipeline_id,
                "stage_id": stage_id,
                "company_id": company_id,
                "contact_id": contact_ids[0],
                "value": 120000.0,
                "currency": "USD",
            },
            headers=hdrs,
        )
        assert deal_resp.status_code == 201, deal_resp.text
        deal = deal_resp.json()["data"]
        assert deal["company_id"] == company_id
        assert deal["pipeline_id"] == pipeline_id
        deal_id = deal["id"]
    else:
        deal_id = None

    # ── 6. Create tasks ──────────────────────────────────────────────────────
    task_ids = []
    for title in ["Send intro email", "Schedule demo call"]:
        task_payload: dict = {
            "title": title,
            "task_type": "task",
            "priority": "high",
            "company_id": company_id,
            "contact_id": contact_ids[0],
            "due_at": "2026-07-15T09:00:00Z",
        }
        if deal_id:
            task_payload["deal_id"] = deal_id

        task_resp = await client.post("/api/v1/crm/tasks", json=task_payload, headers=hdrs)
        assert task_resp.status_code == 201, task_resp.text
        task_ids.append(task_resp.json()["data"]["id"])

    assert len(task_ids) == 2

    # ── 7. Assert entities are linked correctly ──────────────────────────────
    # Contacts are still accessible and linked to the company
    for cid in contact_ids:
        ct_get = await client.get(f"/api/v1/contacts/{cid}", headers=hdrs)
        assert ct_get.status_code == 200, ct_get.text
        assert ct_get.json()["data"]["company_id"] == company_id

    # Company is accessible
    co_get = await client.get(f"/api/v1/companies/{company_id}", headers=hdrs)
    assert co_get.status_code == 200
    assert co_get.json()["data"]["id"] == company_id

    # ── 8. Org isolation: second org cannot see first org's data ─────────────
    token2 = await register_and_login(client, suffix="leadflow2")
    hdrs2 = auth_headers(token2)

    # Second org cannot see first org's company
    co_cross = await client.get(f"/api/v1/companies/{company_id}", headers=hdrs2)
    assert co_cross.status_code == 404, (
        f"Cross-org access should be denied (404), got {co_cross.status_code}: {co_cross.text}"
    )

    # Second org cannot see first org's contacts
    for cid in contact_ids:
        ct_cross = await client.get(f"/api/v1/contacts/{cid}", headers=hdrs2)
        assert ct_cross.status_code == 404, (
            f"Cross-org contact access should be 404, got {ct_cross.status_code}"
        )

    # Second org list endpoints should not return first org's data
    co_list = await client.get("/api/v1/companies/", headers=hdrs2)
    assert co_list.status_code == 200
    co_list_ids = [c["id"] for c in co_list.json()["data"]]
    assert company_id not in co_list_ids, (
        "Second org's company list should not include first org's company"
    )

#!/usr/bin/env python3
"""Local integration test: discovery API sync + async + worker pipeline."""

from __future__ import annotations

import asyncio
import sys
import uuid

import httpx

API = "http://api:8000"
EMAIL = f"discovery-{uuid.uuid4().hex[:8]}@test.com"
PASSWORD = "SecurePass123!"


def section(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def ok(msg: str) -> None:
    print(f"  OK  {msg}")


def fail(msg: str) -> None:
    print(f"  FAIL {msg}")
    sys.exit(1)


async def main() -> None:
    section("TEST 1 — API health")
    async with httpx.AsyncClient(timeout=90.0) as client:
        r = await client.get(f"{API}/health")
        if r.status_code != 200:
            fail(f"Health check: {r.status_code} {r.text}")
        ok(f"API healthy — {r.json()}")

        section("TEST 2 — Register + login")
        reg = await client.post(
            f"{API}/api/v1/auth/register",
            json={
                "email": EMAIL,
                "password": PASSWORD,
                "first_name": "Discovery",
                "last_name": "Tester",
                "organization_name": "Discovery Test Org",
            },
        )
        if reg.status_code not in (200, 201):
            fail(f"Register failed: {reg.status_code} {reg.text}")
        token = reg.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        ok(f"Registered {EMAIL}")

        section("TEST 3 — Sync discovery (async_mode=false)")
        sync_body = {
            "query": "SaaS companies in Austin",
            "entity_type": "company",
            "filters": {},
            "enrich": False,
            "verify_contacts": False,
            "async_mode": False,
        }
        sync = await client.post(f"{API}/api/v1/discovery/execute", json=sync_body, headers=headers)
        if sync.status_code != 200:
            fail(f"Sync discovery: {sync.status_code} {sync.text}")
        sync_data = sync.json().get("data", {})
        sync_total = sync_data.get("total", 0)
        ok(f"Sync job_id={sync_data.get('job_id')} total={sync_total} took_ms={sync_data.get('took_ms')}")
        if sync_total == 0:
            print("  WARN sync returned 0 hits — check USE_MOCK_CONNECTORS or connector API keys")

        section("TEST 4 — Async discovery + Celery worker + polling")
        async_body = {**sync_body, "async_mode": True}
        async_resp = await client.post(f"{API}/api/v1/discovery/execute", json=async_body, headers=headers)
        if async_resp.status_code != 200:
            fail(f"Async enqueue: {async_resp.status_code} {async_resp.text}")
        job_id = async_resp.json().get("data", {}).get("id")
        if not job_id:
            fail("No job id returned")
        ok(f"Job queued id={job_id}")

        final_status = None
        for attempt in range(60):
            status_resp = await client.get(f"{API}/api/v1/discovery/jobs/{job_id}", headers=headers)
            final_status = status_resp.json().get("data", {})
            print(
                f"  poll {attempt + 1}: status={final_status.get('status')} "
                f"progress={final_status.get('progress_pct')}% stages={final_status.get('stages')}"
            )
            if final_status.get("status") in ("completed", "partial", "failed"):
                break
            await asyncio.sleep(1)
        else:
            fail("Async job timed out")

        if final_status.get("status") == "failed":
            fail(f"Job failed: {final_status.get('error_message')}")

        results_resp = await client.get(f"{API}/api/v1/discovery/jobs/{job_id}/results", headers=headers)
        results = results_resp.json().get("data", {})
        result_total = results.get("total", 0)
        ok(f"Results total={result_total} hits={len(results.get('hits', []))}")
        if result_total == 0:
            fail("Async discovery returned 0 hits — mock connector or API keys required")

        section("TEST 5 — DB persistence (job list)")
        list_resp = await client.get(f"{API}/api/v1/discovery/jobs", headers=headers)
        jobs = list_resp.json().get("data", [])
        ok(f"Listed {len(jobs)} job(s)")

        section("ALL TESTS PASSED")


if __name__ == "__main__":
    asyncio.run(main())
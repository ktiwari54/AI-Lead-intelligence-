#!/usr/bin/env python3
"""Local integration test: migration tables, discovery API sync + async, worker pipeline."""

from __future__ import annotations

import asyncio
import sys
import time
import uuid

import httpx

API = "http://localhost:8000"
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
    async with httpx.AsyncClient(timeout=60.0) as client:
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
        ok(f"Sync job_id={sync_data.get('job_id')} total={sync_data.get('total')} took_ms={sync_data.get('took_ms')}")
        if "hits" not in sync_data:
            fail("Sync response missing hits")

        section("TEST 4 — Async discovery + job polling")
        async_body = {**sync_body, "async_mode": True}
        async_resp = await client.post(f"{API}/api/v1/discovery/execute", json=async_body, headers=headers)
        if async_resp.status_code != 200:
            fail(f"Async enqueue: {async_resp.status_code} {async_resp.text}")
        job = async_resp.json().get("data", {})
        job_id = job.get("id")
        if not job_id:
            fail(f"No job id in response: {job}")
        ok(f"Job queued id={job_id}")

        final_status = None
        for attempt in range(45):
            status_resp = await client.get(f"{API}/api/v1/discovery/jobs/{job_id}", headers=headers)
            if status_resp.status_code != 200:
                fail(f"Job status: {status_resp.status_code} {status_resp.text}")
            final_status = status_resp.json().get("data", {})
            stages = final_status.get("stages", {})
            print(f"  poll {attempt + 1}: status={final_status.get('status')} progress={final_status.get('progress_pct')}% stages={stages}")
            if final_status.get("status") in ("completed", "partial", "failed"):
                break
            await asyncio.sleep(1)
        else:
            fail("Async job timed out after 45s")

        if final_status.get("status") == "failed":
            fail(f"Job failed: {final_status.get('error_message')}")

        results_resp = await client.get(f"{API}/api/v1/discovery/jobs/{job_id}/results", headers=headers)
        if results_resp.status_code != 200:
            fail(f"Job results: {results_resp.status_code} {results_resp.text}")
        results = results_resp.json().get("data", {})
        ok(f"Async results total={results.get('total')} hits={len(results.get('hits', []))}")

        section("TEST 5 — List discovery jobs (DB persistence)")
        list_resp = await client.get(f"{API}/api/v1/discovery/jobs", headers=headers)
        if list_resp.status_code != 200:
            fail(f"List jobs: {list_resp.status_code} {list_resp.text}")
        jobs = list_resp.json().get("data", [])
        ok(f"Listed {len(jobs)} job(s) for tenant")

        section("ALL TESTS PASSED")
        print(f"  Sync + async discovery working for {EMAIL}")


if __name__ == "__main__":
    asyncio.run(main())
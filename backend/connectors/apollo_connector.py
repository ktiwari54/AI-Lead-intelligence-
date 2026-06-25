import httpx
from typing import Dict
from connectors.base_connector import BaseConnector, ConnectorResult


class ApolloConnector(BaseConnector):
    name = "apollo"
    credits_per_call = 1
    BASE_URL = "https://api.apollo.io/v1"

    async def authenticate(self) -> bool:
        self._authenticated = await self.health_check()
        return self._authenticated

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    f"{self.BASE_URL}/auth/health",
                    headers={"X-Api-Key": self.config.get("api_key", "")},
                )
                return r.status_code == 200
        except Exception:
            return False

    def get_rate_limit(self) -> Dict:
        return {"requests_per_minute": 50}

    async def search(self, params: Dict) -> ConnectorResult:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(
                    f"{self.BASE_URL}/mixed_people/search",
                    json={**params, "api_key": self.config.get("api_key")},
                )
                return ConnectorResult(success=r.status_code == 200, data=self.normalize(r.json()), credits_used=1)
        except Exception as e:
            return ConnectorResult(success=False, error=str(e))

    async def lookup(self, identifier: str) -> ConnectorResult:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.get(
                    f"{self.BASE_URL}/people/match",
                    params={"email": identifier, "api_key": self.config.get("api_key")},
                )
                return ConnectorResult(success=r.status_code == 200, data=r.json(), credits_used=1)
        except Exception as e:
            return ConnectorResult(success=False, error=str(e))

    async def enrich(self, entity: Dict) -> ConnectorResult:
        return await self.lookup(entity.get("email", ""))

    def normalize(self, raw: Dict) -> Dict:
        people = raw.get("people", [])
        return {
            "total": raw.get("pagination", {}).get("total_entries", 0),
            "contacts": [
                {
                    "first_name": p.get("first_name"),
                    "last_name": p.get("last_name"),
                    "email": p.get("email"),
                    "designation": p.get("title"),
                    "department": p.get("departments", [None])[0],
                    "linkedin_url": p.get("linkedin_url"),
                    "company_name": p.get("organization", {}).get("name"),
                    "company_domain": p.get("organization", {}).get("primary_domain"),
                }
                for p in people
            ],
            "_raw": raw,
        }

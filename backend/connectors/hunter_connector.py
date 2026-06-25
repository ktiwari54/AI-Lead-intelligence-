import httpx
from typing import Dict
from connectors.base_connector import BaseConnector, ConnectorResult


class HunterConnector(BaseConnector):
    name = "hunter"
    credits_per_call = 1
    BASE_URL = "https://api.hunter.io/v2"

    async def authenticate(self) -> bool:
        self._authenticated = await self.health_check()
        return self._authenticated

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"{self.BASE_URL}/account", params={"api_key": self.config.get("api_key")})
                return r.status_code == 200
        except Exception:
            return False

    def get_rate_limit(self) -> Dict:
        return {"requests_per_month": 25, "requests_per_second": 1}

    async def search(self, params: Dict) -> ConnectorResult:
        domain = params.get("domain")
        if not domain:
            return ConnectorResult(success=False, error="domain required")
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.get(
                    f"{self.BASE_URL}/domain-search",
                    params={"domain": domain, "api_key": self.config.get("api_key")},
                )
                return ConnectorResult(success=r.status_code == 200, data=self.normalize(r.json()), credits_used=1)
        except Exception as e:
            return ConnectorResult(success=False, error=str(e))

    async def lookup(self, identifier: str) -> ConnectorResult:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.get(
                    f"{self.BASE_URL}/email-finder",
                    params={"company": identifier, "api_key": self.config.get("api_key")},
                )
                return ConnectorResult(success=r.status_code == 200, data=r.json(), credits_used=1)
        except Exception as e:
            return ConnectorResult(success=False, error=str(e))

    async def enrich(self, entity: Dict) -> ConnectorResult:
        email = entity.get("email")
        if not email:
            return ConnectorResult(success=False, error="email required")
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.get(
                    f"{self.BASE_URL}/email-verifier",
                    params={"email": email, "api_key": self.config.get("api_key")},
                )
                return ConnectorResult(success=r.status_code == 200, data=self.normalize(r.json()), credits_used=1)
        except Exception as e:
            return ConnectorResult(success=False, error=str(e))

    def normalize(self, raw: Dict) -> Dict:
        d = raw.get("data", raw)
        return {
            "email": d.get("email"),
            "status": d.get("status"),
            "score": d.get("score"),
            "first_name": d.get("first_name"),
            "last_name": d.get("last_name"),
            "position": d.get("position"),
            "domain": d.get("domain"),
            "_raw": raw,
        }

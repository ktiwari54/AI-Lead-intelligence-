import httpx
from typing import Dict
from connectors.base_connector import BaseConnector, ConnectorResult


class ClearbitConnector(BaseConnector):
    name = "clearbit"
    credits_per_call = 5
    COMPANY_URL = "https://company.clearbit.com/v2"
    PERSON_URL = "https://person.clearbit.com/v2"

    async def authenticate(self) -> bool:
        self._authenticated = await self.health_check()
        return self._authenticated

    async def health_check(self) -> bool:
        return bool(self.config.get("api_key"))

    def get_rate_limit(self) -> Dict:
        return {"requests_per_minute": 600}

    async def search(self, params: Dict) -> ConnectorResult:
        return ConnectorResult(success=False, error="Use lookup() or enrich() for Clearbit")

    async def lookup(self, identifier: str) -> ConnectorResult:
        try:
            async with httpx.AsyncClient(auth=(self.config["api_key"], ""), timeout=30) as client:
                r = await client.get(f"{self.COMPANY_URL}/companies/find", params={"domain": identifier})
                if r.status_code == 200:
                    return ConnectorResult(success=True, data=self.normalize(r.json()), credits_used=self.credits_per_call)
                return ConnectorResult(success=False, error=f"HTTP {r.status_code}")
        except Exception as e:
            return ConnectorResult(success=False, error=str(e))

    async def enrich(self, entity: Dict) -> ConnectorResult:
        domain = entity.get("domain") or (
            entity.get("website", "").replace("https://", "").replace("http://", "").split("/")[0]
        )
        if not domain:
            return ConnectorResult(success=False, error="domain required")
        return await self.lookup(domain)

    def normalize(self, raw: Dict) -> Dict:
        return {
            "company_name": raw.get("name"),
            "domain": raw.get("domain"),
            "description": raw.get("description"),
            "employee_count": raw.get("metrics", {}).get("employees"),
            "revenue": raw.get("metrics", {}).get("annualRevenue"),
            "founded_year": raw.get("foundedYear"),
            "country": raw.get("geo", {}).get("country"),
            "city": raw.get("geo", {}).get("city"),
            "industry": raw.get("category", {}).get("industry"),
            "technologies": [t.get("tag") for t in raw.get("tech", [])],
            "linkedin_url": raw.get("linkedin", {}).get("handle"),
            "_raw": raw,
        }

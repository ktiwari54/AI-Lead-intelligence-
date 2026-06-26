"""OpenSearch async client and index lifecycle management."""
from opensearchpy import AsyncOpenSearch
from backend.config import get_settings

settings = get_settings()

_client: AsyncOpenSearch | None = None

def get_opensearch() -> AsyncOpenSearch:
    global _client
    if _client is None:
        _client = AsyncOpenSearch(
            hosts=[settings.OPENSEARCH_URL],
            http_compress=True,
            use_ssl=settings.OPENSEARCH_URL.startswith("https"),
            verify_certs=False,
            ssl_show_warn=False,
        )
    return _client


COMPANY_INDEX_MAPPING = {
    "settings": {
        "number_of_shards": 2,
        "number_of_replicas": 1,
        "analysis": {
            "analyzer": {
                "company_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding", "stop"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "organization_id": {"type": "keyword"},
            "name": {"type": "text", "analyzer": "company_analyzer", "fields": {"keyword": {"type": "keyword"}}},
            "domain": {"type": "keyword"},
            "description": {"type": "text", "analyzer": "company_analyzer"},
            "industry": {"type": "keyword"},
            "country": {"type": "keyword"},
            "city": {"type": "keyword"},
            "employee_count": {"type": "integer"},
            "annual_revenue": {"type": "long"},
            "technologies": {"type": "keyword"},
            "overall_score": {"type": "float"},
            "enrichment_status": {"type": "keyword"},
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"},
        }
    }
}

CONTACT_INDEX_MAPPING = {
    "settings": {
        "number_of_shards": 2,
        "number_of_replicas": 1,
        "analysis": {
            "analyzer": {
                "contact_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding", "stop"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "organization_id": {"type": "keyword"},
            "first_name": {"type": "text", "analyzer": "contact_analyzer"},
            "last_name": {"type": "text", "analyzer": "contact_analyzer"},
            "full_name": {"type": "text", "analyzer": "contact_analyzer", "fields": {"keyword": {"type": "keyword"}}},
            "email": {"type": "keyword"},
            "designation": {"type": "text", "analyzer": "contact_analyzer", "fields": {"keyword": {"type": "keyword"}}},
            "department": {"type": "keyword"},
            "seniority": {"type": "keyword"},
            "company_id": {"type": "keyword"},
            "company_name": {"type": "text", "analyzer": "contact_analyzer"},
            "country": {"type": "keyword"},
            "email_status": {"type": "keyword"},
            "overall_score": {"type": "float"},
            "has_phone": {"type": "boolean"},
            "has_linkedin": {"type": "boolean"},
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"},
        }
    }
}


def company_index(org_id: str) -> str:
    return f"{settings.OPENSEARCH_INDEX_PREFIX}_companies_{org_id}"

def contact_index(org_id: str) -> str:
    return f"{settings.OPENSEARCH_INDEX_PREFIX}_contacts_{org_id}"


async def ensure_indices(org_id: str) -> None:
    """Create company and contact indices for org if they don't exist."""
    client = get_opensearch()
    c_idx = company_index(org_id)
    ct_idx = contact_index(org_id)

    if not await client.indices.exists(index=c_idx):
        await client.indices.create(index=c_idx, body=COMPANY_INDEX_MAPPING)

    if not await client.indices.exists(index=ct_idx):
        await client.indices.create(index=ct_idx, body=CONTACT_INDEX_MAPPING)


async def index_company(org_id: str, company: dict) -> None:
    """Index or update a company document."""
    await ensure_indices(org_id)
    client = get_opensearch()
    await client.index(
        index=company_index(org_id),
        id=company["id"],
        body=company,
        refresh="wait_for",
    )


async def index_contact(org_id: str, contact: dict) -> None:
    """Index or update a contact document."""
    await ensure_indices(org_id)
    client = get_opensearch()
    await client.index(
        index=contact_index(org_id),
        id=contact["id"],
        body=contact,
        refresh="wait_for",
    )


async def delete_company(org_id: str, company_id: str) -> None:
    client = get_opensearch()
    idx = company_index(org_id)
    if await client.indices.exists(index=idx):
        await client.delete(index=idx, id=company_id, ignore=[404])


async def delete_contact(org_id: str, contact_id: str) -> None:
    client = get_opensearch()
    idx = contact_index(org_id)
    if await client.indices.exists(index=idx):
        await client.delete(index=idx, id=contact_id, ignore=[404])


async def bulk_index_companies(org_id: str, companies: list[dict]) -> dict:
    """Bulk index a list of company dicts."""
    if not companies:
        return {"indexed": 0}
    await ensure_indices(org_id)
    client = get_opensearch()

    actions = []
    for c in companies:
        actions.append({"index": {"_index": company_index(org_id), "_id": c["id"]}})
        actions.append(c)

    response = await client.bulk(body=actions, refresh="wait_for")
    errors = [item for item in response.get("items", []) if "error" in item.get("index", {})]
    return {"indexed": len(companies) - len(errors), "errors": len(errors)}


async def bulk_index_contacts(org_id: str, contacts: list[dict]) -> dict:
    """Bulk index a list of contact dicts."""
    if not contacts:
        return {"indexed": 0}
    await ensure_indices(org_id)
    client = get_opensearch()

    actions = []
    for c in contacts:
        actions.append({"index": {"_index": contact_index(org_id), "_id": c["id"]}})
        actions.append(c)

    response = await client.bulk(body=actions, refresh="wait_for")
    errors = [item for item in response.get("items", []) if "error" in item.get("index", {})]
    return {"indexed": len(contacts) - len(errors), "errors": len(errors)}

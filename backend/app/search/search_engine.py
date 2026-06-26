"""
Search engine: translates SearchRequest filters into OpenSearch queries.
"""
from dataclasses import dataclass, field
from backend.app.common.opensearch import get_opensearch, company_index, contact_index


@dataclass
class SearchFilters:
    query: str | None = None
    entity_type: str = "both"  # "companies", "contacts", "both"
    industries: list[str] = field(default_factory=list)
    countries: list[str] = field(default_factory=list)
    seniority_levels: list[str] = field(default_factory=list)
    departments: list[str] = field(default_factory=list)
    technologies: list[str] = field(default_factory=list)
    min_employees: int | None = None
    max_employees: int | None = None
    min_revenue: int | None = None
    max_revenue: int | None = None
    min_score: float | None = None
    email_status: str | None = None
    has_phone: bool | None = None
    has_linkedin: bool | None = None
    page: int = 1
    page_size: int = 25
    sort_by: str = "overall_score"
    sort_order: str = "desc"


@dataclass
class SearchHit:
    id: str
    entity_type: str  # "company" or "contact"
    score: float
    data: dict
    highlight: dict = field(default_factory=dict)


@dataclass
class SearchResponse:
    total: int
    page: int
    page_size: int
    hits: list[SearchHit]
    took_ms: int
    aggregations: dict = field(default_factory=dict)


async def execute_search(org_id: str, filters: SearchFilters) -> SearchResponse:
    """Execute a search across companies and/or contacts."""
    client = get_opensearch()

    results: list[SearchHit] = []
    total = 0
    took_ms = 0
    aggregations = {}

    from_ = (filters.page - 1) * filters.page_size

    if filters.entity_type in ("companies", "both"):
        company_resp = await _search_companies(client, org_id, filters, from_)
        total += company_resp["hits"]["total"]["value"]
        took_ms = max(took_ms, company_resp.get("took", 0))

        for hit in company_resp["hits"]["hits"]:
            results.append(SearchHit(
                id=hit["_id"],
                entity_type="company",
                score=hit.get("_score") or 0,
                data=hit["_source"],
                highlight=hit.get("highlight", {}),
            ))

        if "aggregations" in company_resp:
            aggregations["companies"] = company_resp["aggregations"]

    if filters.entity_type in ("contacts", "both"):
        contact_resp = await _search_contacts(client, org_id, filters, from_)
        total += contact_resp["hits"]["total"]["value"]
        took_ms = max(took_ms, contact_resp.get("took", 0))

        for hit in contact_resp["hits"]["hits"]:
            results.append(SearchHit(
                id=hit["_id"],
                entity_type="contact",
                score=hit.get("_score") or 0,
                data=hit["_source"],
                highlight=hit.get("highlight", {}),
            ))

        if "aggregations" in contact_resp:
            aggregations["contacts"] = contact_resp["aggregations"]

    results.sort(key=lambda h: h.score, reverse=(filters.sort_order == "desc"))

    return SearchResponse(
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        hits=results[:filters.page_size],
        took_ms=took_ms,
        aggregations=aggregations,
    )


def _build_base_query(query: str | None) -> dict:
    if not query:
        return {"match_all": {}}
    return {
        "multi_match": {
            "query": query,
            "fields": ["name^3", "full_name^3", "domain^2", "designation^2", "description", "company_name"],
            "type": "best_fields",
            "fuzziness": "AUTO",
            "prefix_length": 2,
        }
    }


def _add_company_filters(must: list, filters: SearchFilters) -> None:
    if filters.industries:
        must.append({"terms": {"industry": filters.industries}})
    if filters.countries:
        must.append({"terms": {"country": filters.countries}})
    if filters.technologies:
        must.append({"terms": {"technologies": filters.technologies}})
    if filters.min_employees is not None or filters.max_employees is not None:
        emp_range = {}
        if filters.min_employees is not None:
            emp_range["gte"] = filters.min_employees
        if filters.max_employees is not None:
            emp_range["lte"] = filters.max_employees
        must.append({"range": {"employee_count": emp_range}})
    if filters.min_revenue is not None or filters.max_revenue is not None:
        rev_range = {}
        if filters.min_revenue is not None:
            rev_range["gte"] = filters.min_revenue
        if filters.max_revenue is not None:
            rev_range["lte"] = filters.max_revenue
        must.append({"range": {"annual_revenue": rev_range}})
    if filters.min_score is not None:
        must.append({"range": {"overall_score": {"gte": filters.min_score}}})


def _add_contact_filters(must: list, filters: SearchFilters) -> None:
    if filters.seniority_levels:
        must.append({"terms": {"seniority": filters.seniority_levels}})
    if filters.departments:
        must.append({"terms": {"department": filters.departments}})
    if filters.countries:
        must.append({"terms": {"country": filters.countries}})
    if filters.email_status:
        must.append({"term": {"email_status": filters.email_status}})
    if filters.has_phone is not None:
        must.append({"term": {"has_phone": filters.has_phone}})
    if filters.has_linkedin is not None:
        must.append({"term": {"has_linkedin": filters.has_linkedin}})
    if filters.min_score is not None:
        must.append({"range": {"overall_score": {"gte": filters.min_score}}})


async def _search_companies(client, org_id: str, filters: SearchFilters, from_: int) -> dict:
    must = [{"term": {"organization_id": org_id}}]
    _add_company_filters(must, filters)

    body = {
        "query": {
            "bool": {
                "must": must,
                "should": [_build_base_query(filters.query)] if filters.query else [],
                "minimum_should_match": 1 if filters.query else 0,
            }
        },
        "from": from_,
        "size": filters.page_size,
        "sort": [{filters.sort_by: {"order": filters.sort_order}}] if not filters.query else ["_score"],
        "highlight": {
            "fields": {"name": {}, "description": {}, "domain": {}},
            "pre_tags": ["<em>"],
            "post_tags": ["</em>"],
        },
        "aggs": {
            "industries": {"terms": {"field": "industry", "size": 20}},
            "countries": {"terms": {"field": "country", "size": 20}},
            "technologies": {"terms": {"field": "technologies", "size": 20}},
        }
    }

    idx = company_index(org_id)
    try:
        return await client.search(index=idx, body=body)
    except Exception:
        return {"hits": {"total": {"value": 0}, "hits": []}, "took": 0}


async def _search_contacts(client, org_id: str, filters: SearchFilters, from_: int) -> dict:
    must = [{"term": {"organization_id": org_id}}]
    _add_contact_filters(must, filters)

    body = {
        "query": {
            "bool": {
                "must": must,
                "should": [_build_base_query(filters.query)] if filters.query else [],
                "minimum_should_match": 1 if filters.query else 0,
            }
        },
        "from": from_,
        "size": filters.page_size,
        "sort": [{filters.sort_by: {"order": filters.sort_order}}] if not filters.query else ["_score"],
        "highlight": {
            "fields": {"full_name": {}, "designation": {}, "company_name": {}},
            "pre_tags": ["<em>"],
            "post_tags": ["</em>"],
        },
        "aggs": {
            "seniority": {"terms": {"field": "seniority", "size": 10}},
            "departments": {"terms": {"field": "department", "size": 20}},
            "countries": {"terms": {"field": "country", "size": 20}},
        }
    }

    idx = contact_index(org_id)
    try:
        return await client.search(index=idx, body=body)
    except Exception:
        return {"hits": {"total": {"value": 0}, "hits": []}, "took": 0}

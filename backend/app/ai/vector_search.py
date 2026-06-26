"""
Vector similarity search using pgvector.

Supports:
- Find companies similar to a given company
- Find contacts similar to a given contact
- Semantic search (natural language query → similar leads)
- "More like this" recommendations
"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field

from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.ai.embeddings import get_embedding


@dataclass
class VectorSearchResult:
    id: uuid.UUID
    entity_type: str  # "company" or "contact"
    similarity: float  # cosine similarity 0-1
    data: dict
    distance: float  # L2 distance


@dataclass
class VectorSearchResponse:
    query: str
    results: list[VectorSearchResult]
    total: int
    embedding_model: str = "text-embedding-3-small"


async def semantic_search_companies(
    db: AsyncSession,
    org_id: uuid.UUID,
    query: str,
    limit: int = 20,
    min_similarity: float = 0.5,
) -> list[VectorSearchResult]:
    """
    Find companies semantically similar to the query text.
    Uses cosine distance (<=> operator in pgvector).
    """
    embedding = await get_embedding(query)
    if not embedding:
        return []

    vector_str = "[" + ",".join(str(x) for x in embedding) + "]"

    result = await db.execute(
        text("""
            SELECT 
                id,
                name,
                industry,
                country,
                employee_count,
                annual_revenue,
                1 - (embedding <=> :embedding::vector) AS similarity,
                (embedding <=> :embedding::vector) AS distance
            FROM core.companies
            WHERE organization_id = :org_id
              AND deleted_at IS NULL
              AND embedding IS NOT NULL
              AND 1 - (embedding <=> :embedding::vector) >= :min_sim
            ORDER BY embedding <=> :embedding::vector
            LIMIT :limit
        """),
        {
            "embedding": vector_str,
            "org_id": str(org_id),
            "min_sim": min_similarity,
            "limit": limit,
        },
    )
    rows = result.mappings().all()
    return [
        VectorSearchResult(
            id=uuid.UUID(str(row["id"])),
            entity_type="company",
            similarity=float(row["similarity"]),
            distance=float(row["distance"]),
            data={
                "name": row["name"],
                "industry": row["industry"],
                "country": row["country"],
                "employee_count": row["employee_count"],
                "annual_revenue": row["annual_revenue"],
            },
        )
        for row in rows
    ]


async def semantic_search_contacts(
    db: AsyncSession,
    org_id: uuid.UUID,
    query: str,
    limit: int = 20,
    min_similarity: float = 0.5,
) -> list[VectorSearchResult]:
    """Find contacts semantically similar to the query text."""
    embedding = await get_embedding(query)
    if not embedding:
        return []

    vector_str = "[" + ",".join(str(x) for x in embedding) + "]"

    result = await db.execute(
        text("""
            SELECT 
                c.id,
                c.first_name,
                c.last_name,
                c.email,
                c.designation,
                c.department,
                c.seniority,
                co.name AS company_name,
                1 - (c.embedding <=> :embedding::vector) AS similarity,
                (c.embedding <=> :embedding::vector) AS distance
            FROM core.contacts c
            LEFT JOIN core.companies co ON co.id = c.company_id
            WHERE c.organization_id = :org_id
              AND c.deleted_at IS NULL
              AND c.embedding IS NOT NULL
              AND 1 - (c.embedding <=> :embedding::vector) >= :min_sim
            ORDER BY c.embedding <=> :embedding::vector
            LIMIT :limit
        """),
        {
            "embedding": vector_str,
            "org_id": str(org_id),
            "min_sim": min_similarity,
            "limit": limit,
        },
    )
    rows = result.mappings().all()
    return [
        VectorSearchResult(
            id=uuid.UUID(str(row["id"])),
            entity_type="contact",
            similarity=float(row["similarity"]),
            distance=float(row["distance"]),
            data={
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "email": row["email"],
                "designation": row["designation"],
                "department": row["department"],
                "seniority": row["seniority"],
                "company_name": row["company_name"],
            },
        )
        for row in rows
    ]


async def find_similar_companies(
    db: AsyncSession,
    org_id: uuid.UUID,
    company_id: uuid.UUID,
    limit: int = 10,
) -> list[VectorSearchResult]:
    """Find companies similar to a specific company (More Like This)."""
    result = await db.execute(
        text("""
            SELECT embedding FROM core.companies
            WHERE id = :company_id AND organization_id = :org_id
        """),
        {"company_id": str(company_id), "org_id": str(org_id)},
    )
    row = result.fetchone()
    if not row or row[0] is None:
        return []

    embedding_str = str(row[0])

    result2 = await db.execute(
        text("""
            SELECT 
                id, name, industry, country, employee_count,
                1 - (embedding <=> :embedding::vector) AS similarity,
                (embedding <=> :embedding::vector) AS distance
            FROM core.companies
            WHERE organization_id = :org_id
              AND deleted_at IS NULL
              AND id != :company_id
              AND embedding IS NOT NULL
            ORDER BY embedding <=> :embedding::vector
            LIMIT :limit
        """),
        {"embedding": embedding_str, "org_id": str(org_id), "company_id": str(company_id), "limit": limit},
    )
    rows = result2.mappings().all()
    return [
        VectorSearchResult(
            id=uuid.UUID(str(row["id"])),
            entity_type="company",
            similarity=float(row["similarity"]),
            distance=float(row["distance"]),
            data={"name": row["name"], "industry": row["industry"], "country": row["country"], "employee_count": row["employee_count"]},
        )
        for row in rows
    ]


async def find_similar_contacts(
    db: AsyncSession,
    org_id: uuid.UUID,
    contact_id: uuid.UUID,
    limit: int = 10,
) -> list[VectorSearchResult]:
    """Find contacts similar to a specific contact."""
    result = await db.execute(
        text("SELECT embedding FROM core.contacts WHERE id = :cid AND organization_id = :oid"),
        {"cid": str(contact_id), "oid": str(org_id)},
    )
    row = result.fetchone()
    if not row or row[0] is None:
        return []

    result2 = await db.execute(
        text("""
            SELECT c.id, c.first_name, c.last_name, c.designation, c.seniority,
                   1 - (c.embedding <=> :embedding::vector) AS similarity,
                   (c.embedding <=> :embedding::vector) AS distance
            FROM core.contacts c
            WHERE c.organization_id = :oid AND c.deleted_at IS NULL
              AND c.id != :cid AND c.embedding IS NOT NULL
            ORDER BY c.embedding <=> :embedding::vector
            LIMIT :limit
        """),
        {"embedding": str(row[0]), "oid": str(org_id), "cid": str(contact_id), "limit": limit},
    )
    rows = result2.mappings().all()
    return [
        VectorSearchResult(
            id=uuid.UUID(str(r["id"])),
            entity_type="contact",
            similarity=float(r["similarity"]),
            distance=float(r["distance"]),
            data={"first_name": r["first_name"], "last_name": r["last_name"], "designation": r["designation"], "seniority": r["seniority"]},
        )
        for r in rows
    ]

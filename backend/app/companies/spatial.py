"""
PostGIS spatial search for companies.

Enables queries like:
- "Companies within 50 km of Dubai"
- "Manufacturers near Chennai Port"
- "Tech companies in the San Francisco Bay Area"

We store company coordinates as PostGIS GEOGRAPHY(POINT, 4326) which:
- Uses WGS84 coordinate system (same as GPS/Google Maps)
- Gives accurate distance calculations in meters on a spherical Earth
- Enables efficient radius search using ST_DWithin (uses spatial index)
"""
from __future__ import annotations
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class GeoPoint:
    latitude: float   # -90 to 90
    longitude: float  # -180 to 180

    def to_wkt(self) -> str:
        """Well-Known Text for PostGIS: POINT(longitude latitude)"""
        return f"POINT({self.longitude} {self.latitude})"


@dataclass
class SpatialCompanyResult:
    id: UUID
    name: str
    domain: str | None
    industry: str | None
    country: str | None
    city: str | None
    employee_count: int | None
    latitude: float | None
    longitude: float | None
    distance_km: float
    overall_score: float | None = None


@dataclass
class SpatialSearchRequest:
    latitude: float
    longitude: float
    radius_km: float = 50.0
    industry: str | None = None
    min_employees: int | None = None
    max_employees: int | None = None
    min_score: float | None = None
    limit: int = 50
    offset: int = 0


async def search_companies_near(
    db: AsyncSession,
    org_id: UUID,
    request: SpatialSearchRequest,
) -> list[SpatialCompanyResult]:
    """
    Find companies within a geographic radius using PostGIS ST_DWithin.
    ST_DWithin on GEOGRAPHY type computes accurate spherical distances.
    The spatial index (GIST) makes this O(log n) instead of O(n).
    """
    # Build optional filter clauses
    filters = ["c.organization_id = :org_id", "c.deleted_at IS NULL", "c.location IS NOT NULL"]
    params: dict = {
        "org_id": str(org_id),
        "origin": f"SRID=4326;POINT({request.longitude} {request.latitude})",
        "radius_m": request.radius_km * 1000,
        "limit": request.limit,
        "offset": request.offset,
    }

    if request.industry:
        filters.append("c.industry = :industry")
        params["industry"] = request.industry

    if request.min_employees is not None:
        filters.append("c.employee_count >= :min_emp")
        params["min_emp"] = request.min_employees

    if request.max_employees is not None:
        filters.append("c.employee_count <= :max_emp")
        params["max_emp"] = request.max_employees

    if request.min_score is not None:
        filters.append("ls.overall_score >= :min_score")
        params["min_score"] = request.min_score

    where_clause = " AND ".join(filters)

    result = await db.execute(
        text(f"""
            SELECT
                c.id,
                c.name,
                c.domain,
                c.industry,
                c.country,
                c.city,
                c.employee_count,
                ST_Y(c.location::geometry) AS latitude,
                ST_X(c.location::geometry) AS longitude,
                ST_Distance(c.location, ST_GeographyFromText(:origin)) / 1000.0 AS distance_km,
                ls.overall_score
            FROM core.companies c
            LEFT JOIN ai.lead_scores ls 
                ON ls.company_id = c.id 
                AND ls.organization_id = c.organization_id
            WHERE {where_clause}
              AND ST_DWithin(
                  c.location,
                  ST_GeographyFromText(:origin),
                  :radius_m
              )
            ORDER BY c.location <-> ST_GeographyFromText(:origin)
            LIMIT :limit OFFSET :offset
        """),
        params,
    )

    rows = result.mappings().all()
    return [
        SpatialCompanyResult(
            id=UUID(str(row["id"])),
            name=row["name"],
            domain=row["domain"],
            industry=row["industry"],
            country=row["country"],
            city=row["city"],
            employee_count=row["employee_count"],
            latitude=float(row["latitude"]) if row["latitude"] else None,
            longitude=float(row["longitude"]) if row["longitude"] else None,
            distance_km=round(float(row["distance_km"]), 2),
            overall_score=float(row["overall_score"]) if row["overall_score"] else None,
        )
        for row in rows
    ]


async def count_companies_near(
    db: AsyncSession,
    org_id: UUID,
    latitude: float,
    longitude: float,
    radius_km: float,
) -> int:
    """Count companies within radius (for pagination total)."""
    result = await db.execute(
        text("""
            SELECT COUNT(*) FROM core.companies
            WHERE organization_id = :org_id
              AND deleted_at IS NULL
              AND location IS NOT NULL
              AND ST_DWithin(
                  location,
                  ST_GeographyFromText(:origin),
                  :radius_m
              )
        """),
        {
            "org_id": str(org_id),
            "origin": f"SRID=4326;POINT({longitude} {latitude})",
            "radius_m": radius_km * 1000,
        },
    )
    return result.scalar() or 0


async def set_company_location(
    db: AsyncSession,
    org_id: UUID,
    company_id: UUID,
    latitude: float,
    longitude: float,
) -> bool:
    """Set or update a company's geographic location."""
    result = await db.execute(
        text("""
            UPDATE core.companies
            SET 
                location = ST_GeographyFromText(:point),
                latitude = :lat,
                longitude = :lon,
                updated_at = now()
            WHERE id = :company_id AND organization_id = :org_id
            RETURNING id
        """),
        {
            "point": f"SRID=4326;POINT({longitude} {latitude})",
            "lat": latitude,
            "lon": longitude,
            "company_id": str(company_id),
            "org_id": str(org_id),
        },
    )
    return result.fetchone() is not None


async def geocode_companies_without_location(
    db: AsyncSession,
    org_id: UUID,
    limit: int = 100,
) -> list[dict]:
    """Return companies that have city/country but no geo coordinates yet."""
    result = await db.execute(
        text("""
            SELECT id, name, city, country
            FROM core.companies
            WHERE organization_id = :org_id
              AND deleted_at IS NULL
              AND location IS NULL
              AND (city IS NOT NULL OR country IS NOT NULL)
            LIMIT :limit
        """),
        {"org_id": str(org_id), "limit": limit},
    )
    return [dict(row) for row in result.mappings().all()]

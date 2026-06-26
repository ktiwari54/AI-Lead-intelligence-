"""postgis_spatial: add geography columns for spatial company search

Revision ID: 005
Revises: 004
Create Date: 2025-01-01
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure PostGIS is available
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis_topology")
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    # Add geography column to companies for point location
    # GEOGRAPHY type uses WGS84 (SRID 4326) and computes distances in meters on a sphere
    op.execute("""
        ALTER TABLE core.companies
        ADD COLUMN IF NOT EXISTS location geography(POINT, 4326)
    """)

    # Also store raw lat/lon as floats for easy access without PostGIS
    op.execute("""
        ALTER TABLE core.companies
        ADD COLUMN IF NOT EXISTS latitude double precision,
        ADD COLUMN IF NOT EXISTS longitude double precision
    """)

    # GIST index on geography column — enables fast ST_DWithin radius queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_companies_location_gist
        ON core.companies
        USING gist(location)
        WHERE location IS NOT NULL AND deleted_at IS NULL
    """)

    # KNN index using <-> operator for ordered distance scans
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_companies_location_knn
        ON core.companies
        USING gist(location)
        WHERE location IS NOT NULL
    """)

    # Add bounding box column for region-based searches (e.g., companies IN a polygon)
    # Useful for "companies in the San Francisco Bay Area" queries
    op.execute("""
        ALTER TABLE core.countries
        ADD COLUMN IF NOT EXISTS bounding_box geography(POLYGON, 4326)
    """)

    op.execute("""
        ALTER TABLE core.cities
        ADD COLUMN IF NOT EXISTS location geography(POINT, 4326),
        ADD COLUMN IF NOT EXISTS latitude double precision,
        ADD COLUMN IF NOT EXISTS longitude double precision
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_cities_location_gist
        ON core.cities
        USING gist(location)
        WHERE location IS NOT NULL
    """)

    # Trigger to keep location in sync with lat/lon columns
    op.execute("""
        CREATE OR REPLACE FUNCTION sync_company_location()
        RETURNS trigger AS $$
        BEGIN
            IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
                NEW.location := ST_GeographyFromText(
                    'SRID=4326;POINT(' || NEW.longitude || ' ' || NEW.latitude || ')'
                );
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        DROP TRIGGER IF EXISTS trg_sync_company_location ON core.companies;
        CREATE TRIGGER trg_sync_company_location
        BEFORE INSERT OR UPDATE OF latitude, longitude ON core.companies
        FOR EACH ROW EXECUTE FUNCTION sync_company_location();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_sync_company_location ON core.companies")
    op.execute("DROP FUNCTION IF EXISTS sync_company_location()")
    op.execute("DROP INDEX IF EXISTS idx_companies_location_gist")
    op.execute("DROP INDEX IF EXISTS idx_companies_location_knn")
    op.execute("DROP INDEX IF EXISTS idx_cities_location_gist")
    op.execute("ALTER TABLE core.companies DROP COLUMN IF EXISTS location")
    op.execute("ALTER TABLE core.companies DROP COLUMN IF EXISTS latitude")
    op.execute("ALTER TABLE core.companies DROP COLUMN IF EXISTS longitude")
    op.execute("ALTER TABLE core.countries DROP COLUMN IF EXISTS bounding_box")
    op.execute("ALTER TABLE core.cities DROP COLUMN IF EXISTS location")
    op.execute("ALTER TABLE core.cities DROP COLUMN IF EXISTS latitude")
    op.execute("ALTER TABLE core.cities DROP COLUMN IF EXISTS longitude")

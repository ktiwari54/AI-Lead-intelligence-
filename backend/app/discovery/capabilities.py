from __future__ import annotations

from enum import Enum


class ConnectorCapability(str, Enum):
    """Capability-based connector classification — providers are plugins behind these."""

    SEARCH = "search"
    LOOKUP = "lookup"
    FETCH_DETAILS = "fetch_details"
    ENRICH = "enrich"
    VERIFY_EMAIL = "verify_email"
    VERIFY_PHONE = "verify_phone"
    DETECT_TECH = "detect_tech"
    GEOCODE = "geocode"
    CRM_SYNC = "crm_sync"
    IMPORT = "import"
    WEBHOOK = "webhook"


class DataSourceType(str, Enum):
    """Legal/ethical classification of data origin."""

    OFFICIAL_API = "official_api"
    LICENSED_PROVIDER = "licensed_provider"
    PUBLIC_REGISTRY = "public_registry"
    GOVERNMENT_OPEN_DATA = "government_open_data"
    USER_AUTHORIZED = "user_authorized"
    USER_IMPORT = "user_import"
    SEARCH_INDEX = "search_index"


class ConnectorCategory(str, Enum):
    SEARCH_PROVIDER = "search_provider"
    BUSINESS_DIRECTORY = "business_directory"
    COMPANY_REGISTRY = "company_registry"
    GOVERNMENT_DATA = "government_data"
    ENRICHMENT = "enrichment"
    VERIFICATION = "verification"
    TECH_DETECTION = "tech_detection"
    CRM = "crm"
    IMPORT = "import"
    WEBHOOK = "webhook"
    NEWS = "news"
    GEOLOCATION = "geolocation"
    AI = "ai"
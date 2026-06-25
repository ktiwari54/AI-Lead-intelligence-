from app.models.identity import Organization
from app.organizations.schemas import OrganizationUpdate


async def update_organization(org: Organization, data: OrganizationUpdate) -> Organization:
    for k, v in data.model_dump(exclude_none=True, exclude_unset=True).items():
        setattr(org, k, v)
    return org

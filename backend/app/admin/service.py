from __future__ import annotations
from datetime import datetime, timedelta, timezone
from uuid import UUID
from typing import Any

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.models import AuditLog, SystemSetting, FeatureFlag
from backend.app.admin.schemas import SystemSettingUpdate, FeatureFlagUpdate, AdminStatsResponse
from backend.app.organizations.models import Organization
from backend.app.users.models import User
from backend.app.companies.models import Company
from backend.app.contacts.models import Contact
from backend.app.search.models import Search
from backend.app.exports.models import Export
from backend.app.common.exceptions import NotFoundError


class AdminService:

    async def create_audit_log(
        self, db: AsyncSession, org_id: UUID | None, user_id: UUID | None,
        action: str, resource_type: str, resource_id: str | None = None,
        old_values: dict | None = None, new_values: dict | None = None,
        ip_address: str | None = None, user_agent: str | None = None,
    ) -> AuditLog:
        log = AuditLog(
            organization_id=org_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(log)
        await db.flush()
        return log

    async def list_audit_logs(
        self, db: AsyncSession, org_id: UUID | None = None,
        resource_type: str | None = None, user_id: UUID | None = None,
        page: int = 1, page_size: int = 50,
    ) -> tuple[list[AuditLog], int]:
        q = select(AuditLog)
        if org_id:
            q = q.where(AuditLog.organization_id == org_id)
        if resource_type:
            q = q.where(AuditLog.resource_type == resource_type)
        if user_id:
            q = q.where(AuditLog.user_id == user_id)

        total = await db.scalar(select(func.count()).select_from(q.subquery())) or 0
        result = await db.execute(
            q.order_by(AuditLog.created_at.desc())
            .offset((page - 1) * page_size).limit(page_size)
        )
        return result.scalars().all(), total

    async def get_system_settings(self, db: AsyncSession, public_only: bool = False) -> list[SystemSetting]:
        q = select(SystemSetting)
        if public_only:
            q = q.where(SystemSetting.is_public == True)
        result = await db.execute(q.order_by(SystemSetting.key))
        return result.scalars().all()

    async def get_setting(self, db: AsyncSession, key: str) -> SystemSetting | None:
        result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
        return result.scalar_one_or_none()

    async def update_setting(self, db: AsyncSession, key: str, data: SystemSettingUpdate) -> SystemSetting:
        setting = await self.get_setting(db, key)
        if not setting:
            raise NotFoundError(f"Setting '{key}' not found")
        if not setting.is_editable:
            from backend.app.common.exceptions import ForbiddenError
            raise ForbiddenError(f"Setting '{key}' is not editable")
        setting.value = data.value
        if data.description is not None:
            setting.description = data.description
        await db.flush()
        return setting

    async def upsert_setting(self, db: AsyncSession, key: str, value: Any, description: str | None = None, is_public: bool = False) -> SystemSetting:
        setting = await self.get_setting(db, key)
        if setting:
            setting.value = value
        else:
            setting = SystemSetting(key=key, value=value, description=description, is_public=is_public, is_editable=True)
            db.add(setting)
        await db.flush()
        return setting

    async def list_feature_flags(self, db: AsyncSession) -> list[FeatureFlag]:
        result = await db.execute(select(FeatureFlag).order_by(FeatureFlag.key))
        return result.scalars().all()

    async def get_feature_flag(self, db: AsyncSession, key: str) -> FeatureFlag | None:
        result = await db.execute(select(FeatureFlag).where(FeatureFlag.key == key))
        return result.scalar_one_or_none()

    async def update_feature_flag(self, db: AsyncSession, key: str, data: FeatureFlagUpdate) -> FeatureFlag:
        flag = await self.get_feature_flag(db, key)
        if not flag:
            raise NotFoundError(f"Feature flag '{key}' not found")
        if data.is_enabled is not None:
            flag.is_enabled = data.is_enabled
        if data.rollout_percentage is not None:
            flag.rollout_percentage = max(0, min(100, data.rollout_percentage))
        if data.allowed_org_ids is not None:
            flag.allowed_org_ids = data.allowed_org_ids
        await db.flush()
        return flag

    def is_feature_enabled(self, flag: FeatureFlag | None, org_id: UUID | None = None) -> bool:
        if not flag or not flag.is_enabled:
            return False
        if flag.allowed_org_ids and org_id and str(org_id) in flag.allowed_org_ids:
            return True
        if flag.rollout_percentage >= 100:
            return True
        if flag.rollout_percentage == 0:
            return False
        if org_id:
            return (int(str(org_id).replace("-", ""), 16) % 100) < flag.rollout_percentage
        return False

    async def get_admin_stats(self, db: AsyncSession) -> AdminStatsResponse:
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        return AdminStatsResponse(
            total_organizations=await db.scalar(select(func.count()).select_from(Organization).where(Organization.deleted_at.is_(None))) or 0,
            total_users=await db.scalar(select(func.count()).select_from(User).where(User.deleted_at.is_(None))) or 0,
            total_companies=await db.scalar(select(func.count()).select_from(Company).where(Company.deleted_at.is_(None))) or 0,
            total_contacts=await db.scalar(select(func.count()).select_from(Contact).where(Contact.deleted_at.is_(None))) or 0,
            total_searches_today=await db.scalar(select(func.count()).select_from(Search).where(Search.created_at >= today)) or 0,
            total_exports_pending=await db.scalar(select(func.count()).select_from(Export).where(Export.status == "PENDING")) or 0,
        )

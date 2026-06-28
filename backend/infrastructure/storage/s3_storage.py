from __future__ import annotations

from typing import Protocol
from uuid import UUID


class StoragePort(Protocol):
    async def generate_upload_url(
        self, org_id: UUID, purpose: str, filename: str, content_type: str
    ) -> dict: ...

    async def generate_download_url(self, key: str, expires_in: int = 900) -> str: ...

    async def delete(self, key: str) -> None: ...


class S3Storage:
    """S3-compatible object storage adapter."""

    def __init__(self, bucket: str, endpoint_url: str | None = None, region: str = "us-east-1"):
        self.bucket = bucket
        self.endpoint_url = endpoint_url
        self.region = region

    def _key(self, org_id: UUID, purpose: str, file_id: str, filename: str) -> str:
        return f"{org_id}/{purpose}/{file_id}/{filename}"

    async def generate_upload_url(
        self, org_id: UUID, purpose: str, filename: str, content_type: str
    ) -> dict:
        from backend.app.common.uuid7 import uuid7

        file_id = str(uuid7())
        key = self._key(org_id, purpose, file_id, filename)
        # Production: boto3 generate_presigned_url
        return {
            "file_id": file_id,
            "key": key,
            "upload_url": f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}",
            "content_type": content_type,
            "expires_in": 900,
        }

    async def generate_download_url(self, key: str, expires_in: int = 900) -> str:
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}?expires={expires_in}"

    async def delete(self, key: str) -> None:
        pass  # Production: boto3 delete_object
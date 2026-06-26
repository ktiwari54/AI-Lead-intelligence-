from __future__ import annotations
import io
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.common.dependencies import get_current_user, get_db
from backend.app.common.schemas import PaginatedResponse
from backend.app.exports.schemas import (
    ExportCreate,
    ExportResponse,
    ImportJobCreate,
    ImportJobResponse,
)
from backend.app.exports.service import ExportService
from backend.workers.tasks.export import generate_export_task

router = APIRouter(prefix="/exports", tags=["Exports"])
service = ExportService()

_CONTENT_TYPES = {
    "CSV": "text/csv",
    "JSON": "application/json",
    "EXCEL": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

_FILE_EXTENSIONS = {
    "CSV": "csv",
    "JSON": "json",
    "EXCEL": "xlsx",
}


@router.post("/", response_model=ExportResponse, status_code=201)
async def create_export(
    body: ExportCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    export = await service.create_export(
        db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
        data=body,
    )
    await db.commit()
    await db.refresh(export)
    generate_export_task.delay(str(export.id), str(current_user.organization_id))
    return ExportResponse.model_validate(export)


@router.get("/", response_model=PaginatedResponse[ExportResponse])
async def list_exports(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    items, total = await service.list_exports(
        db,
        org_id=current_user.organization_id,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[ExportResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/imports/{job_id}", response_model=ImportJobResponse)
async def get_import_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    job = await service.get_import_job(db, org_id=current_user.organization_id, job_id=job_id)
    return ImportJobResponse.model_validate(job)


@router.post("/imports", response_model=ImportJobResponse, status_code=201)
async def create_import_job(
    body: ImportJobCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    job = await service.create_import_job(
        db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
        data=body,
    )
    await db.commit()
    await db.refresh(job)
    return ImportJobResponse.model_validate(job)


@router.get("/{export_id}", response_model=ExportResponse)
async def get_export(
    export_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    export = await service.get_export(db, org_id=current_user.organization_id, export_id=export_id)
    return ExportResponse.model_validate(export)


@router.get("/{export_id}/download")
async def download_export(
    export_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    org_id = current_user.organization_id
    export = await service.get_export(db, org_id=org_id, export_id=export_id)

    if export.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Export not ready")

    fmt = export.format
    if fmt == "JSON":
        content = await service.generate_json_export(db, org_id=org_id, export_id=export_id)
    else:
        content = await service.generate_csv_export(db, org_id=org_id, export_id=export_id)

    await db.commit()

    ext = _FILE_EXTENSIONS.get(fmt, "csv")
    filename = f"{export.name}.{ext}"
    media_type = _CONTENT_TYPES.get(fmt, "text/csv")

    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{export_id}", status_code=204)
async def delete_export(
    export_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    export = await service.get_export(db, org_id=current_user.organization_id, export_id=export_id)
    await db.delete(export)
    await db.commit()

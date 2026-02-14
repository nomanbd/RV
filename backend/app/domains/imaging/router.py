import uuid

from fastapi import APIRouter, Depends, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.domains.auth.models import User
from app.domains.imaging.schemas import (
    ImageResponse,
    ImageReviewCreate,
    ImageReviewResponse,
)
from app.domains.imaging.service import ImagingService

router = APIRouter(prefix="/imaging", tags=["imaging"])


@router.post("/images/import", response_model=ImageResponse, status_code=201)
async def import_image(
    file: UploadFile,
    patient_id: uuid.UUID = Query(...),
    session_id: uuid.UUID | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file_bytes = await file.read()
    service = ImagingService(db)
    return await service.import_image(
        file_bytes=file_bytes,
        filename=file.filename or "unknown.dcm",
        patient_id=patient_id,
        session_id=session_id,
    )


@router.get("/images", response_model=list[ImageResponse])
async def list_images(
    patient_id: uuid.UUID | None = Query(None),
    session_id: uuid.UUID | None = Query(None),
    image_type: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ImagingService(db)
    return await service.list_images(
        patient_id=patient_id,
        session_id=session_id,
        image_type=image_type,
    )


@router.get("/images/{image_id}", response_model=ImageResponse)
async def get_image(
    image_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ImagingService(db)
    return await service.get_image(image_id)


@router.post("/images/{image_id}/review", response_model=ImageReviewResponse, status_code=201)
async def create_review(
    image_id: uuid.UUID,
    data: ImageReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Ensure the image_id in the path is used
    data.image_id = image_id
    service = ImagingService(db)
    return await service.create_review(data, reviewer_id=current_user.id)


@router.post("/reviews/{review_id}/apply-shifts", response_model=ImageReviewResponse)
async def apply_shifts(
    review_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ImagingService(db)
    return await service.apply_shifts(review_id, user_id=current_user.id)

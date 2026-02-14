import io
import uuid
from datetime import datetime, timezone

import pydicom
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError, ValidationError
from app.dicom.parsers.rt_image import RTImageParser
from app.dicom.storage.file_manager import DicomFileManager
from app.domains.imaging.models import ImageReview, RTImage
from app.domains.imaging.schemas import ImageReviewCreate


class ImagingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.parser = RTImageParser()
        self.file_manager = DicomFileManager()

    async def import_image(
        self,
        file_bytes: bytes,
        filename: str,
        patient_id: uuid.UUID,
        session_id: uuid.UUID | None = None,
    ) -> RTImage:
        """Parse a DICOM image file, store it on disk, and create a database record."""
        # Parse the DICOM data
        ds = pydicom.dcmread(io.BytesIO(file_bytes))
        parsed = self.parser.parse(ds)
        image_type = self.parser.classify_image_type(ds)

        # Store the file
        file_path = self.file_manager.store(ds, patient_id=str(patient_id))
        file_size = len(file_bytes)

        # Parse acquisition date/time
        acq_date = None
        if parsed.get("acquisition_date"):
            try:
                acq_date = datetime.strptime(parsed["acquisition_date"], "%Y%m%d").date()
            except (ValueError, TypeError):
                pass

        acq_time = None
        if parsed.get("acquisition_time"):
            try:
                time_str = parsed["acquisition_time"].split(".")[0]  # Remove fractional seconds
                acq_time = datetime.strptime(time_str, "%H%M%S").time()
            except (ValueError, TypeError):
                pass

        image = RTImage(
            patient_id=patient_id,
            session_id=session_id,
            sop_instance_uid=parsed["sop_instance_uid"],
            series_instance_uid=parsed.get("series_instance_uid"),
            study_instance_uid=parsed.get("study_instance_uid"),
            image_type=image_type,
            acquisition_date=acq_date,
            acquisition_time=acq_time,
            gantry_angle=parsed.get("gantry_angle"),
            beam_name=parsed.get("beam_name"),
            image_plane=parsed.get("rt_image_plane"),
            rows=parsed.get("rows"),
            columns=parsed.get("columns"),
            pixel_spacing=parsed.get("pixel_spacing"),
            file_path=file_path,
            file_size_bytes=file_size,
            dicom_metadata=parsed,
        )
        self.db.add(image)
        await self.db.flush()
        return image

    async def get_image(self, image_id: uuid.UUID) -> RTImage:
        result = await self.db.execute(
            select(RTImage)
            .options(selectinload(RTImage.reviews))
            .where(RTImage.id == image_id)
        )
        image = result.scalar_one_or_none()
        if image is None:
            raise NotFoundError("Image not found")
        return image

    async def list_images(
        self,
        patient_id: uuid.UUID | None = None,
        session_id: uuid.UUID | None = None,
        image_type: str | None = None,
    ) -> list[RTImage]:
        query = select(RTImage)
        if patient_id is not None:
            query = query.where(RTImage.patient_id == patient_id)
        if session_id is not None:
            query = query.where(RTImage.session_id == session_id)
        if image_type is not None:
            query = query.where(RTImage.image_type == image_type)
        query = query.order_by(RTImage.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_review(
        self, data: ImageReviewCreate, reviewer_id: uuid.UUID
    ) -> ImageReview:
        # Verify the image exists
        image = await self.get_image(data.image_id)

        now = datetime.now(timezone.utc)
        review = ImageReview(
            image_id=data.image_id,
            session_id=image.session_id,
            reviewer_id=reviewer_id,
            status="reviewed",
            shift_vertical_cm=data.shift_vertical_cm,
            shift_lateral_cm=data.shift_lateral_cm,
            shift_longitudinal_cm=data.shift_longitudinal_cm,
            rotation_pitch_deg=data.rotation_pitch_deg,
            rotation_roll_deg=data.rotation_roll_deg,
            rotation_yaw_deg=data.rotation_yaw_deg,
            review_type=data.review_type,
            comments=data.comments,
            reviewed_at=now,
        )
        self.db.add(review)
        await self.db.flush()
        return review

    async def apply_shifts(
        self, review_id: uuid.UUID, user_id: uuid.UUID
    ) -> ImageReview:
        """Mark image review shifts as applied to the treatment couch."""
        result = await self.db.execute(
            select(ImageReview).where(ImageReview.id == review_id)
        )
        review = result.scalar_one_or_none()
        if review is None:
            raise NotFoundError("Image review not found")

        if review.shifts_applied:
            raise ValidationError("Shifts have already been applied for this review")

        now = datetime.now(timezone.utc)
        review.shifts_applied = True
        review.shifts_applied_at = now
        review.shifts_applied_by_id = user_id

        await self.db.flush()
        return review

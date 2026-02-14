"""
DICOM File Storage Manager.

Manages storage and retrieval of DICOM files on disk, organized by:
  dicom_storage/{patient_id}/{study_uid}/{series_uid}/{sop_uid}.dcm
"""

import logging
import os
from pathlib import Path

import pydicom
from pydicom.dataset import Dataset

from app.core.config import settings

logger = logging.getLogger(__name__)


class DicomFileManager:
    """Manages DICOM file storage on disk."""

    def __init__(self, base_path: str | None = None):
        self.base_path = Path(base_path or settings.DICOM_STORAGE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def store(self, ds: Dataset, patient_id: str | None = None) -> str:
        """Store a DICOM dataset to disk.

        Args:
            ds: DICOM dataset to store
            patient_id: Optional patient ID override (uses DICOM PatientID if not provided)

        Returns:
            Relative file path from base_path
        """
        pid = patient_id or str(getattr(ds, "PatientID", "unknown"))
        study_uid = str(getattr(ds, "StudyInstanceUID", "unknown_study"))
        series_uid = str(getattr(ds, "SeriesInstanceUID", "unknown_series"))
        sop_uid = str(ds.SOPInstanceUID)

        # Create directory structure
        dir_path = self.base_path / pid / study_uid / series_uid
        dir_path.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = dir_path / f"{sop_uid}.dcm"
        ds.save_as(str(file_path))

        # Return relative path
        return str(file_path.relative_to(self.base_path))

    def retrieve(self, relative_path: str) -> Dataset:
        """Retrieve a DICOM dataset from disk.

        Args:
            relative_path: Relative path from base storage directory

        Returns:
            pydicom Dataset
        """
        full_path = self.base_path / relative_path
        if not full_path.exists():
            raise FileNotFoundError(f"DICOM file not found: {relative_path}")
        return pydicom.dcmread(str(full_path))

    def get_full_path(self, relative_path: str) -> Path:
        """Get the full filesystem path for a relative DICOM path."""
        return self.base_path / relative_path

    def delete(self, relative_path: str) -> bool:
        """Delete a DICOM file from storage.

        Args:
            relative_path: Relative path from base storage directory

        Returns:
            True if file was deleted, False if it didn't exist
        """
        full_path = self.base_path / relative_path
        if full_path.exists():
            full_path.unlink()
            # Clean up empty parent directories
            for parent in full_path.parents:
                if parent == self.base_path:
                    break
                if parent.is_dir() and not any(parent.iterdir()):
                    parent.rmdir()
            return True
        return False

    def get_file_size(self, relative_path: str) -> int:
        """Get the size of a stored DICOM file in bytes."""
        full_path = self.base_path / relative_path
        if not full_path.exists():
            return 0
        return full_path.stat().st_size

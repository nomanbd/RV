"""
DICOM RT Image Parser.

Handles RT Images (portal, DRR), CT images, and kV/MV images.
"""

import logging
from typing import Any

from pydicom.dataset import Dataset

logger = logging.getLogger(__name__)


class RTImageParser:
    """Parse DICOM RT Image and related image datasets."""

    def parse(self, ds: Dataset) -> dict[str, Any]:
        """Parse an image DICOM dataset (RT Image, CT, kV, MV)."""
        image_data: dict[str, Any] = {
            "sop_instance_uid": str(ds.SOPInstanceUID),
            "sop_class_uid": str(ds.SOPClassUID),
            "series_instance_uid": str(getattr(ds, "SeriesInstanceUID", "")),
            "study_instance_uid": str(getattr(ds, "StudyInstanceUID", "")),
            "modality": str(getattr(ds, "Modality", "")),
        }

        # Image dimensions
        image_data["rows"] = int(getattr(ds, "Rows", 0))
        image_data["columns"] = int(getattr(ds, "Columns", 0))

        # Pixel spacing
        if hasattr(ds, "PixelSpacing"):
            image_data["pixel_spacing"] = [float(s) for s in ds.PixelSpacing]
        elif hasattr(ds, "ImagePlanePixelSpacing"):
            image_data["pixel_spacing"] = [float(s) for s in ds.ImagePlanePixelSpacing]

        # Patient and study info
        image_data["patient_id"] = str(getattr(ds, "PatientID", ""))
        image_data["patient_name"] = str(getattr(ds, "PatientName", ""))

        # Acquisition
        image_data["acquisition_date"] = str(getattr(ds, "AcquisitionDate", getattr(ds, "ContentDate", "")))
        image_data["acquisition_time"] = str(getattr(ds, "AcquisitionTime", getattr(ds, "ContentTime", "")))

        # RT-specific fields
        if hasattr(ds, "RTImagePlane"):
            image_data["rt_image_plane"] = str(ds.RTImagePlane)
        if hasattr(ds, "GantryAngle"):
            image_data["gantry_angle"] = float(ds.GantryAngle)
        if hasattr(ds, "BeamLimitingDeviceAngle"):
            image_data["collimator_angle"] = float(ds.BeamLimitingDeviceAngle)
        if hasattr(ds, "ReferencedBeamNumber"):
            image_data["referenced_beam_number"] = int(ds.ReferencedBeamNumber)

        # Window center/width for display
        if hasattr(ds, "WindowCenter"):
            wc = ds.WindowCenter
            image_data["window_center"] = float(wc[0]) if isinstance(wc, (list, pydicom.multival.MultiValue)) else float(wc)
        if hasattr(ds, "WindowWidth"):
            ww = ds.WindowWidth
            image_data["window_width"] = float(ww[0]) if isinstance(ww, (list, pydicom.multival.MultiValue)) else float(ww)

        # Image position and orientation (for CT, CBCT)
        if hasattr(ds, "ImagePositionPatient"):
            image_data["image_position"] = [float(p) for p in ds.ImagePositionPatient]
        if hasattr(ds, "ImageOrientationPatient"):
            image_data["image_orientation"] = [float(o) for o in ds.ImageOrientationPatient]

        # Machine reference
        image_data["station_name"] = str(getattr(ds, "StationName", ""))
        image_data["manufacturer"] = str(getattr(ds, "Manufacturer", ""))

        return image_data

    def classify_image_type(self, ds: Dataset) -> str:
        """Determine the image type based on SOP Class and modality."""
        sop_class = str(ds.SOPClassUID) if hasattr(ds, "SOPClassUID") else ""
        modality = str(getattr(ds, "Modality", ""))

        # RT Image SOP Class
        if sop_class == "1.2.840.10008.5.1.4.1.1.481.1":
            return "portal"
        # CT Image
        elif sop_class == "1.2.840.10008.5.1.4.1.1.2":
            if modality == "CT":
                return "cbct"
            return "cbct"
        # Digital X-Ray
        elif sop_class in ("1.2.840.10008.5.1.4.1.1.1.1", "1.2.840.10008.5.1.4.1.1.12.1"):
            return "kv_kv"

        # Fallback
        if hasattr(ds, "RTImagePlane"):
            return "drr"
        return "portal"


# Need to import pydicom for MultiValue check
import pydicom

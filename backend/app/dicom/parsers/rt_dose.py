"""
DICOM RT Dose Parser.

Extracts dose distribution data from DICOM RT Dose files, including:
- Dose grid data (3D array)
- Dose summation type
- DVH sequences (if present)
- Referenced RT Plan
"""

import logging
from typing import Any

import numpy as np
import pydicom
from pydicom.dataset import Dataset

logger = logging.getLogger(__name__)


class RTDoseParser:
    """Parse DICOM RT Dose datasets."""

    def parse(self, ds: Dataset) -> dict[str, Any]:
        """Parse a complete RT Dose DICOM dataset."""
        dose_data: dict[str, Any] = {
            "sop_instance_uid": str(ds.SOPInstanceUID),
            "dose_summation_type": str(getattr(ds, "DoseSummationType", "PLAN")),
            "dose_units": str(getattr(ds, "DoseUnits", "GY")),
            "dose_type": str(getattr(ds, "DoseType", "PHYSICAL")),
        }

        # Referenced RT Plan
        if hasattr(ds, "ReferencedRTPlanSequence") and len(ds.ReferencedRTPlanSequence) > 0:
            dose_data["referenced_plan_uid"] = str(ds.ReferencedRTPlanSequence[0].ReferencedSOPInstanceUID)

        # Grid dimensions
        dose_data["rows"] = int(getattr(ds, "Rows", 0))
        dose_data["columns"] = int(getattr(ds, "Columns", 0))
        dose_data["number_of_frames"] = int(getattr(ds, "NumberOfFrames", 1))

        # Pixel spacing and position
        if hasattr(ds, "PixelSpacing"):
            dose_data["pixel_spacing"] = [float(s) for s in ds.PixelSpacing]
        if hasattr(ds, "ImagePositionPatient"):
            dose_data["image_position"] = [float(p) for p in ds.ImagePositionPatient]
        if hasattr(ds, "GridFrameOffsetVector"):
            dose_data["grid_frame_offsets"] = [float(o) for o in ds.GridFrameOffsetVector]

        # Dose grid scaling
        dose_data["dose_grid_scaling"] = float(getattr(ds, "DoseGridScaling", 1.0))

        # Extract dose statistics
        try:
            pixel_array = ds.pixel_array.astype(np.float64)
            scaled_dose = pixel_array * dose_data["dose_grid_scaling"]
            dose_data["max_dose_gy"] = float(np.max(scaled_dose))
            dose_data["mean_dose_gy"] = float(np.mean(scaled_dose[scaled_dose > 0]))
        except Exception as e:
            logger.warning(f"Could not extract dose grid: {e}")
            dose_data["max_dose_gy"] = None
            dose_data["mean_dose_gy"] = None

        # DVH sequences
        dose_data["dvh_data"] = self._parse_dvh(ds)

        return dose_data

    def _parse_dvh(self, ds: Dataset) -> list[dict[str, Any]]:
        """Extract Dose Volume Histogram data if present."""
        dvh_list = []
        if not hasattr(ds, "DVHSequence"):
            return dvh_list

        for dvh in ds.DVHSequence:
            dvh_entry: dict[str, Any] = {
                "dvh_type": str(getattr(dvh, "DVHType", "CUMULATIVE")),
                "dose_units": str(getattr(dvh, "DoseUnits", "GY")),
                "dvh_dose_scaling": float(getattr(dvh, "DVHDoseScaling", 1.0)),
                "dvh_volume_units": str(getattr(dvh, "DVHVolumeUnits", "CM3")),
            }

            # Referenced ROI
            if hasattr(dvh, "DVHReferencedROISequence") and len(dvh.DVHReferencedROISequence) > 0:
                dvh_entry["referenced_roi_number"] = int(dvh.DVHReferencedROISequence[0].ReferencedROINumber)

            # Min/Mean/Max doses
            dvh_entry["dvh_minimum_dose"] = float(getattr(dvh, "DVHMinimumDose", 0))
            dvh_entry["dvh_maximum_dose"] = float(getattr(dvh, "DVHMaximumDose", 0))
            dvh_entry["dvh_mean_dose"] = float(getattr(dvh, "DVHMeanDose", 0))

            # DVH data points
            if hasattr(dvh, "DVHData"):
                dvh_entry["dvh_data_points"] = [float(d) for d in dvh.DVHData]

            dvh_list.append(dvh_entry)

        return dvh_list

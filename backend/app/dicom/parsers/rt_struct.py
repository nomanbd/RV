"""
DICOM RT Structure Set Parser.

Extracts structure set data from DICOM RT Structure Set files, including:
- Structure Set metadata
- ROI definitions (names, types, colors)
- Contour data for each ROI
"""

import logging
from typing import Any

from pydicom.dataset import Dataset

logger = logging.getLogger(__name__)


class RTStructParser:
    """Parse DICOM RT Structure Set datasets."""

    def parse(self, ds: Dataset) -> dict[str, Any]:
        """Parse a complete RT Structure Set DICOM dataset."""
        struct_data: dict[str, Any] = {
            "sop_instance_uid": str(ds.SOPInstanceUID),
            "structure_set_label": str(getattr(ds, "StructureSetLabel", "")),
            "structure_set_date": str(getattr(ds, "StructureSetDate", "")),
        }

        # Referenced Frame of Reference
        if hasattr(ds, "ReferencedFrameOfReferenceSequence"):
            for ref in ds.ReferencedFrameOfReferenceSequence:
                struct_data["frame_of_reference_uid"] = str(ref.FrameOfReferenceUID)
                break

        # Parse ROIs
        roi_definitions = self._parse_roi_definitions(ds)
        roi_observations = self._parse_roi_observations(ds)
        roi_contours = self._parse_roi_contours(ds)

        # Merge ROI data
        rois = []
        for roi_num, roi_def in roi_definitions.items():
            roi: dict[str, Any] = {**roi_def}
            if roi_num in roi_observations:
                roi.update(roi_observations[roi_num])
            if roi_num in roi_contours:
                roi["contour_data"] = roi_contours[roi_num]
            else:
                roi["contour_data"] = {"color": None, "contours": []}
            rois.append(roi)

        struct_data["rois"] = rois
        return struct_data

    def _parse_roi_definitions(self, ds: Dataset) -> dict[int, dict]:
        """Extract ROI definitions from StructureSetROISequence."""
        rois = {}
        if not hasattr(ds, "StructureSetROISequence"):
            return rois

        for roi_seq in ds.StructureSetROISequence:
            roi_number = int(roi_seq.ROINumber)
            rois[roi_number] = {
                "roi_number": roi_number,
                "roi_name": str(getattr(roi_seq, "ROIName", f"ROI_{roi_number}")),
                "roi_generation_algorithm": str(getattr(roi_seq, "ROIGenerationAlgorithm", "")),
                "referenced_frame_of_reference_uid": str(
                    getattr(roi_seq, "ReferencedFrameOfReferenceUID", "")
                ),
            }

        return rois

    def _parse_roi_observations(self, ds: Dataset) -> dict[int, dict]:
        """Extract ROI observations (interpreted type, label)."""
        observations = {}
        if not hasattr(ds, "RTROIObservationsSequence"):
            return observations

        for obs in ds.RTROIObservationsSequence:
            roi_number = int(obs.ReferencedROINumber)
            observations[roi_number] = {
                "roi_observation_label": str(getattr(obs, "ROIObservationLabel", "")),
                "rt_roi_interpreted_type": str(getattr(obs, "RTROIInterpretedType", "")),
            }

        return observations

    def _parse_roi_contours(self, ds: Dataset) -> dict[int, dict]:
        """Extract contour data from ROIContourSequence."""
        contours_by_roi = {}
        if not hasattr(ds, "ROIContourSequence"):
            return contours_by_roi

        for roi_contour in ds.ROIContourSequence:
            roi_number = int(roi_contour.ReferencedROINumber)

            # Display color
            color = None
            if hasattr(roi_contour, "ROIDisplayColor"):
                color = [int(c) for c in roi_contour.ROIDisplayColor]

            contours = []
            if hasattr(roi_contour, "ContourSequence"):
                for contour in roi_contour.ContourSequence:
                    contour_data = {
                        "geometric_type": str(getattr(contour, "ContourGeometricType", "CLOSED_PLANAR")),
                        "number_of_points": int(getattr(contour, "NumberOfContourPoints", 0)),
                    }
                    if hasattr(contour, "ContourData"):
                        contour_data["points"] = [float(p) for p in contour.ContourData]
                    contours.append(contour_data)

            contours_by_roi[roi_number] = {
                "color": color,
                "contours": contours,
                "num_contours": len(contours),
            }

        return contours_by_roi

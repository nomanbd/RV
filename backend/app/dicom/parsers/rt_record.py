"""
DICOM RT Beams Treatment Record Parser.

Parses RT Beams Treatment Records that document actual treatment delivery parameters.
"""

import logging
from typing import Any

from pydicom.dataset import Dataset

logger = logging.getLogger(__name__)


class RTRecordParser:
    """Parse DICOM RT Beams Treatment Record datasets."""

    def parse(self, ds: Dataset) -> dict[str, Any]:
        """Parse an RT Beams Treatment Record."""
        record: dict[str, Any] = {
            "sop_instance_uid": str(ds.SOPInstanceUID),
            "treatment_date": str(getattr(ds, "TreatmentDate", "")),
            "treatment_time": str(getattr(ds, "TreatmentTime", "")),
        }

        # Referenced RT Plan
        if hasattr(ds, "ReferencedRTPlanSequence") and len(ds.ReferencedRTPlanSequence) > 0:
            record["referenced_plan_uid"] = str(ds.ReferencedRTPlanSequence[0].ReferencedSOPInstanceUID)

        # Treatment session records
        beams_delivered = []
        if hasattr(ds, "TreatmentSessionBeamSequence"):
            for beam_record in ds.TreatmentSessionBeamSequence:
                beams_delivered.append(self._parse_beam_record(beam_record))

        record["beams_delivered"] = beams_delivered
        return record

    def _parse_beam_record(self, beam_seq: Dataset) -> dict[str, Any]:
        """Parse a single treatment session beam record."""
        beam: dict[str, Any] = {
            "referenced_beam_number": int(getattr(beam_seq, "ReferencedBeamNumber", 0)),
            "treatment_delivery_type": str(getattr(beam_seq, "TreatmentDeliveryType", "TREATMENT")),
            "current_fraction_number": int(getattr(beam_seq, "CurrentFractionNumber", 0)),
            "treatment_verification_status": str(getattr(beam_seq, "TreatmentVerificationStatus", "")),
        }

        # Delivered meterset (MU)
        if hasattr(beam_seq, "DeliveredMeterset"):
            beam["delivered_mu"] = float(beam_seq.DeliveredMeterset)

        # Specified meterset (planned MU for this fraction)
        if hasattr(beam_seq, "SpecifiedMeterset"):
            beam["specified_mu"] = float(beam_seq.SpecifiedMeterset)

        # Treatment machine
        beam["treatment_machine_name"] = str(getattr(beam_seq, "TreatmentMachineName", ""))

        # Control point delivery records
        control_points = []
        if hasattr(beam_seq, "ControlPointDeliverySequence"):
            for cp in beam_seq.ControlPointDeliverySequence:
                cp_data: dict[str, Any] = {
                    "referenced_control_point_index": int(getattr(cp, "ReferencedControlPointIndex", 0)),
                    "delivered_meterset": float(getattr(cp, "DeliveredMeterset", 0)),
                }

                if hasattr(cp, "NominalBeamEnergy"):
                    cp_data["energy_mev"] = float(cp.NominalBeamEnergy)
                if hasattr(cp, "GantryAngle"):
                    cp_data["gantry_angle"] = float(cp.GantryAngle)
                if hasattr(cp, "BeamLimitingDeviceAngle"):
                    cp_data["collimator_angle"] = float(cp.BeamLimitingDeviceAngle)
                if hasattr(cp, "PatientSupportAngle"):
                    cp_data["couch_angle"] = float(cp.PatientSupportAngle)
                if hasattr(cp, "DoseRateDelivered"):
                    cp_data["dose_rate_delivered"] = float(cp.DoseRateDelivered)

                control_points.append(cp_data)

        beam["control_point_records"] = control_points
        return beam

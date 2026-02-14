"""
DICOM RT Plan Parser.

Extracts treatment plan parameters from DICOM RT Plan files, including:
- Plan-level metadata (label, geometry, frame of reference)
- Beam sequences (energy, type, delivery mode)
- Control point sequences (gantry/collimator/couch angles, jaw/MLC positions)
- Fraction group sequences (planned fractions, beam meterset/MU)

DICOM RT Plan IOD reference: PS3.3 C.8.8.9
"""

import logging
from typing import Any

import pydicom
from pydicom.dataset import Dataset

logger = logging.getLogger(__name__)


class RTPlanParser:
    """Parse DICOM RT Plan datasets into structured data for database storage."""

    def parse(self, ds: Dataset) -> dict[str, Any]:
        """Parse a complete RT Plan DICOM dataset.

        Args:
            ds: pydicom Dataset of an RT Plan SOP instance

        Returns:
            Dictionary with keys: plan, beams, fraction_groups, dicom_metadata
        """
        plan_data = self._parse_plan_metadata(ds)
        beams = self._parse_beams(ds)
        fraction_groups = self._parse_fraction_groups(ds)

        # Cross-reference MU from fraction groups to beams
        for fg in fraction_groups:
            for beam in beams:
                if beam["beam_number"] in fg["beam_meterset"]:
                    beam["planned_mu"] = fg["beam_meterset"][beam["beam_number"]]

        return {
            "plan": plan_data,
            "beams": beams,
            "fraction_groups": fraction_groups,
            "dicom_metadata": self._extract_metadata(ds),
        }

    def _parse_plan_metadata(self, ds: Dataset) -> dict[str, Any]:
        """Extract plan-level metadata."""
        plan = {
            "sop_instance_uid": str(ds.SOPInstanceUID),
            "plan_label": str(getattr(ds, "RTPlanLabel", "Unknown")),
            "plan_name": str(getattr(ds, "RTPlanName", "")) or None,
            "plan_geometry": str(getattr(ds, "RTPlanGeometry", "PATIENT")),
        }

        # Frame of reference
        if hasattr(ds, "ReferencedFrameOfReferenceSequence"):
            for ref in ds.ReferencedFrameOfReferenceSequence:
                plan["frame_of_reference_uid"] = str(ref.FrameOfReferenceUID)
                break

        # Referenced Structure Set
        plan["referenced_structure_set_uid"] = self._get_referenced_sop_uid(
            ds, "ReferencedStructureSetSequence"
        )

        # Referenced Dose
        plan["referenced_dose_uid"] = self._get_referenced_sop_uid(
            ds, "ReferencedDoseSequence"
        )

        return plan

    def _parse_beams(self, ds: Dataset) -> list[dict[str, Any]]:
        """Extract all beams from the BeamSequence."""
        beams = []
        if not hasattr(ds, "BeamSequence"):
            return beams

        for idx, beam_seq in enumerate(ds.BeamSequence):
            beam = self._parse_single_beam(beam_seq, idx)
            beams.append(beam)

        return beams

    def _parse_single_beam(self, beam_seq: Dataset, sequence_order: int) -> dict[str, Any]:
        """Extract parameters from a single beam sequence item."""
        beam: dict[str, Any] = {
            "beam_number": int(beam_seq.BeamNumber),
            "beam_name": str(getattr(beam_seq, "BeamName", f"Beam {beam_seq.BeamNumber}")),
            "beam_type": str(beam_seq.BeamType),
            "radiation_type": str(beam_seq.RadiationType),
            "treatment_delivery_type": str(getattr(beam_seq, "TreatmentDeliveryType", "TREATMENT")),
            "num_control_points": int(beam_seq.NumberOfControlPoints),
            "beam_sequence_order": sequence_order,
            "treatment_machine_name": str(getattr(beam_seq, "TreatmentMachineName", "")),
            "planned_mu": None,  # Will be filled from FractionGroupSequence
        }

        # Energy from first control point
        if hasattr(beam_seq, "ControlPointSequence") and len(beam_seq.ControlPointSequence) > 0:
            first_cp = beam_seq.ControlPointSequence[0]
            if hasattr(first_cp, "NominalBeamEnergy"):
                energy_mev = float(first_cp.NominalBeamEnergy)
                beam["energy_mev"] = energy_mev
                beam["energy_label"] = self._get_energy_label(beam_seq, energy_mev)

        # Dose rate
        if hasattr(beam_seq, "ControlPointSequence") and len(beam_seq.ControlPointSequence) > 0:
            first_cp = beam_seq.ControlPointSequence[0]
            if hasattr(first_cp, "DoseRateSet"):
                beam["dose_rate_mu_per_min"] = float(first_cp.DoseRateSet)

        # Wedge info
        if hasattr(beam_seq, "WedgeSequence") and len(beam_seq.WedgeSequence) > 0:
            wedge = beam_seq.WedgeSequence[0]
            beam["wedge_type"] = str(getattr(wedge, "WedgeType", ""))
            beam["wedge_angle"] = float(getattr(wedge, "WedgeAngle", 0))

        # Bolus
        if hasattr(beam_seq, "BolusSequence") and len(beam_seq.BolusSequence) > 0:
            beam["bolus_description"] = str(getattr(beam_seq.BolusSequence[0], "BolusDescription", ""))

        # Parse control points
        beam["control_points"] = self._parse_control_points(beam_seq)

        # Extract initial beam geometry from first control point
        if beam["control_points"]:
            first_cp_data = beam["control_points"][0]
            for key in ("gantry_angle", "collimator_angle", "couch_angle",
                        "jaw_x1", "jaw_x2", "jaw_y1", "jaw_y2",
                        "isocenter_x", "isocenter_y", "isocenter_z"):
                if key in first_cp_data and first_cp_data[key] is not None:
                    beam[key] = first_cp_data[key]

            # Gantry rotation direction
            beam["gantry_rotation"] = first_cp_data.get("gantry_rotation_direction", "NONE")

        return beam

    def _parse_control_points(self, beam_seq: Dataset) -> list[dict[str, Any]]:
        """Extract all control points from a beam sequence.

        DICOM Note: The first control point must contain all parameters.
        Subsequent control points only contain parameters that changed.
        We track the "current" state and propagate unchanged values.
        """
        control_points = []
        if not hasattr(beam_seq, "ControlPointSequence"):
            return control_points

        # Track current state for inherited values
        current_state: dict[str, Any] = {}

        for cp in beam_seq.ControlPointSequence:
            cp_data = self._parse_single_control_point(cp, current_state)
            control_points.append(cp_data)

            # Update current state with any new values
            for key, value in cp_data.items():
                if value is not None and key != "control_point_index" and key != "cumulative_meterset_weight":
                    current_state[key] = value

        return control_points

    def _parse_single_control_point(self, cp: Dataset, inherited: dict) -> dict[str, Any]:
        """Parse a single control point, inheriting unspecified values from previous CP."""
        data: dict[str, Any] = {
            "control_point_index": int(cp.ControlPointIndex),
            "cumulative_meterset_weight": float(cp.CumulativeMetersetWeight),
        }

        # Gantry
        if hasattr(cp, "GantryAngle"):
            data["gantry_angle"] = float(cp.GantryAngle)
        else:
            data["gantry_angle"] = inherited.get("gantry_angle")

        if hasattr(cp, "GantryRotationDirection"):
            data["gantry_rotation_direction"] = str(cp.GantryRotationDirection)
        else:
            data["gantry_rotation_direction"] = inherited.get("gantry_rotation_direction")

        # Collimator
        if hasattr(cp, "BeamLimitingDeviceAngle"):
            data["collimator_angle"] = float(cp.BeamLimitingDeviceAngle)
        else:
            data["collimator_angle"] = inherited.get("collimator_angle")

        # Couch / Patient Support
        if hasattr(cp, "PatientSupportAngle"):
            data["couch_angle"] = float(cp.PatientSupportAngle)
        else:
            data["couch_angle"] = inherited.get("couch_angle")

        # Isocenter position
        if hasattr(cp, "IsocenterPosition"):
            iso = cp.IsocenterPosition
            data["isocenter_x"] = float(iso[0])
            data["isocenter_y"] = float(iso[1])
            data["isocenter_z"] = float(iso[2])
        else:
            data["isocenter_x"] = inherited.get("isocenter_x")
            data["isocenter_y"] = inherited.get("isocenter_y")
            data["isocenter_z"] = inherited.get("isocenter_z")

        # Jaw and MLC positions from BeamLimitingDevicePositionSequence
        data["jaw_x1"] = inherited.get("jaw_x1")
        data["jaw_x2"] = inherited.get("jaw_x2")
        data["jaw_y1"] = inherited.get("jaw_y1")
        data["jaw_y2"] = inherited.get("jaw_y2")
        data["mlc_positions"] = inherited.get("mlc_positions")

        if hasattr(cp, "BeamLimitingDevicePositionSequence"):
            for bld in cp.BeamLimitingDevicePositionSequence:
                device_type = str(bld.RTBeamLimitingDeviceType)
                positions = [float(p) for p in bld.LeafJawPositions]

                if device_type in ("ASYMX", "X"):
                    data["jaw_x1"] = positions[0]
                    data["jaw_x2"] = positions[1]
                elif device_type in ("ASYMY", "Y"):
                    data["jaw_y1"] = positions[0]
                    data["jaw_y2"] = positions[1]
                elif device_type in ("MLCX", "MLCY"):
                    half = len(positions) // 2
                    data["mlc_positions"] = {
                        "bank_a": positions[:half],
                        "bank_b": positions[half:],
                    }

        return data

    def _parse_fraction_groups(self, ds: Dataset) -> list[dict[str, Any]]:
        """Extract fraction group information (planned fractions and beam MU)."""
        groups = []
        if not hasattr(ds, "FractionGroupSequence"):
            return groups

        for fg in ds.FractionGroupSequence:
            fg_data: dict[str, Any] = {
                "fraction_group_number": int(fg.FractionGroupNumber),
                "num_fractions_planned": int(getattr(fg, "NumberOfFractionsPlanned", 0)),
                "beam_meterset": {},
            }

            if hasattr(fg, "ReferencedBeamSequence"):
                for ref_beam in fg.ReferencedBeamSequence:
                    beam_num = int(ref_beam.ReferencedBeamNumber)
                    meterset = float(getattr(ref_beam, "BeamMeterset", 0))
                    fg_data["beam_meterset"][beam_num] = meterset

            groups.append(fg_data)

        return groups

    def _get_energy_label(self, beam_seq: Dataset, energy_mev: float) -> str:
        """Derive a human-readable energy label (e.g., '6MV', '6FFF', '9MeV')."""
        radiation_type = str(beam_seq.RadiationType).upper()

        # Check for FFF (flattening filter free) — look at FluenceMode
        is_fff = False
        if hasattr(beam_seq, "PrimaryFluenceModeSequence"):
            for fm in beam_seq.PrimaryFluenceModeSequence:
                if hasattr(fm, "FluenceMode") and str(fm.FluenceMode) == "NON_STANDARD":
                    is_fff = True

        if radiation_type == "PHOTON":
            suffix = "FFF" if is_fff else "MV"
            return f"{int(energy_mev)}{suffix}"
        elif radiation_type == "ELECTRON":
            return f"{int(energy_mev)}MeV"
        else:
            return f"{energy_mev}"

    def _get_referenced_sop_uid(self, ds: Dataset, sequence_name: str) -> str | None:
        """Extract referenced SOP Instance UID from a sequence."""
        if hasattr(ds, sequence_name):
            seq = getattr(ds, sequence_name)
            if len(seq) > 0 and hasattr(seq[0], "ReferencedSOPInstanceUID"):
                return str(seq[0].ReferencedSOPInstanceUID)
        return None

    def _extract_metadata(self, ds: Dataset) -> dict:
        """Extract key metadata elements for JSON storage."""
        metadata = {}
        for tag_name in (
            "PatientName", "PatientID", "StudyDate", "StudyInstanceUID",
            "SeriesInstanceUID", "Manufacturer", "StationName",
            "SoftwareVersions", "RTPlanDate", "RTPlanTime",
        ):
            if hasattr(ds, tag_name):
                val = getattr(ds, tag_name)
                metadata[tag_name] = str(val) if val else None
        return metadata


def parse_rt_plan_file(filepath: str) -> dict:
    """Convenience function to parse an RT Plan DICOM file from disk."""
    ds = pydicom.dcmread(filepath)
    parser = RTPlanParser()
    return parser.parse(ds)

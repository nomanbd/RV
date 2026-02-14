"""
Radiotherapy Beam Parameter Verification Engine.

Safety-critical component: Compares actual machine parameters against planned values
within tolerance tables. Uses Decimal arithmetic for precision.

Safety constraints:
- All tolerance comparisons use Decimal types (never float) to avoid IEEE 754 precision issues
- Angle comparisons handle 360-degree wraparound correctly
- Energy must be an exact match (not tolerance-based)
- Failed verification is ALWAYS logged to audit trail
- Override requires separate e-signature with "authorization" meaning
"""

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation


@dataclass
class ParameterCheck:
    """Result of a single parameter verification check."""

    name: str
    planned_value: Decimal | str | None
    actual_value: Decimal | str | None
    deviation: Decimal | None
    tolerance: Decimal | None
    result: str  # 'pass', 'fail', 'skip', 'exact_match', 'exact_fail'

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "planned": str(self.planned_value) if self.planned_value is not None else None,
            "actual": str(self.actual_value) if self.actual_value is not None else None,
            "deviation": str(self.deviation) if self.deviation is not None else None,
            "tolerance": str(self.tolerance) if self.tolerance is not None else None,
            "result": self.result,
        }


@dataclass
class VerificationResult:
    """Aggregate result of all parameter checks for a beam."""

    overall_result: str  # 'pass' or 'fail'
    parameter_results: list[ParameterCheck] = field(default_factory=list)
    out_of_tolerance: list[ParameterCheck] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "overall_result": self.overall_result,
            "parameter_results": [p.to_dict() for p in self.parameter_results],
            "out_of_tolerance": [p.to_dict() for p in self.out_of_tolerance],
            "total_checks": len(self.parameter_results),
            "passed_checks": len([p for p in self.parameter_results if p.result in ("pass", "skip", "exact_match")]),
            "failed_checks": len(self.out_of_tolerance),
        }


@dataclass
class BeamParameters:
    """Beam parameters for verification (planned or actual)."""

    gantry_angle: Decimal | None = None
    collimator_angle: Decimal | None = None
    couch_angle: Decimal | None = None
    couch_vertical: Decimal | None = None
    couch_lateral: Decimal | None = None
    couch_longitudinal: Decimal | None = None
    jaw_x1: Decimal | None = None
    jaw_x2: Decimal | None = None
    jaw_y1: Decimal | None = None
    jaw_y2: Decimal | None = None
    energy: str | None = None
    dose_rate: Decimal | None = None
    mu: Decimal | None = None
    mlc_positions: list[Decimal] | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "BeamParameters":
        """Create from dictionary, converting values to Decimal."""

        def to_decimal(val) -> Decimal | None:
            if val is None:
                return None
            try:
                return Decimal(str(val))
            except (InvalidOperation, ValueError):
                return None

        mlc = data.get("mlc_positions")
        mlc_decimals = None
        if mlc is not None:
            mlc_decimals = [Decimal(str(v)) for v in mlc]

        return cls(
            gantry_angle=to_decimal(data.get("gantry_angle")),
            collimator_angle=to_decimal(data.get("collimator_angle")),
            couch_angle=to_decimal(data.get("couch_angle")),
            couch_vertical=to_decimal(data.get("couch_vertical")),
            couch_lateral=to_decimal(data.get("couch_lateral")),
            couch_longitudinal=to_decimal(data.get("couch_longitudinal")),
            jaw_x1=to_decimal(data.get("jaw_x1")),
            jaw_x2=to_decimal(data.get("jaw_x2")),
            jaw_y1=to_decimal(data.get("jaw_y1")),
            jaw_y2=to_decimal(data.get("jaw_y2")),
            energy=data.get("energy"),
            dose_rate=to_decimal(data.get("dose_rate")),
            mu=to_decimal(data.get("mu")),
            mlc_positions=mlc_decimals,
        )


@dataclass
class ToleranceValues:
    """Tolerance values for verification."""

    gantry_angle_tol: Decimal | None = None
    collimator_angle_tol: Decimal | None = None
    couch_angle_tol: Decimal | None = None
    couch_vertical_tol: Decimal | None = None
    couch_lateral_tol: Decimal | None = None
    couch_longitudinal_tol: Decimal | None = None
    jaw_x1_tol: Decimal | None = None
    jaw_x2_tol: Decimal | None = None
    jaw_y1_tol: Decimal | None = None
    jaw_y2_tol: Decimal | None = None
    mlc_tol: Decimal | None = None
    energy_tol: Decimal | None = None  # Not used — energy is exact match
    dose_rate_tol: Decimal | None = None
    mu_tol: Decimal | None = None

    @classmethod
    def from_model(cls, tol_table) -> "ToleranceValues":
        """Create from a ToleranceTable ORM model."""

        def to_decimal(val) -> Decimal | None:
            if val is None:
                return None
            return Decimal(str(val))

        return cls(
            gantry_angle_tol=to_decimal(tol_table.gantry_angle_tol),
            collimator_angle_tol=to_decimal(tol_table.collimator_angle_tol),
            couch_angle_tol=to_decimal(tol_table.couch_angle_tol),
            couch_vertical_tol=to_decimal(tol_table.couch_vertical_tol),
            couch_lateral_tol=to_decimal(tol_table.couch_lateral_tol),
            couch_longitudinal_tol=to_decimal(tol_table.couch_longitudinal_tol),
            jaw_x1_tol=to_decimal(tol_table.jaw_x1_tol),
            jaw_x2_tol=to_decimal(tol_table.jaw_x2_tol),
            jaw_y1_tol=to_decimal(tol_table.jaw_y1_tol),
            jaw_y2_tol=to_decimal(tol_table.jaw_y2_tol),
            mlc_tol=to_decimal(tol_table.mlc_tol),
            energy_tol=to_decimal(tol_table.energy_tol),
            dose_rate_tol=to_decimal(tol_table.dose_rate_tol),
            mu_tol=to_decimal(tol_table.mu_tol),
        )


class VerificationEngine:
    """
    Core verification engine for radiotherapy treatment delivery.

    Compares actual machine parameters against planned parameters within
    the configured tolerance table. This is the single most safety-critical
    component in the R&V system.
    """

    def verify_beam(
        self, planned: BeamParameters, actual: BeamParameters, tolerance: ToleranceValues
    ) -> VerificationResult:
        """
        Compare actual machine parameters against planned values within tolerances.

        Returns VerificationResult with:
        - overall_result: 'pass' if all checks pass, 'fail' if any check fails
        - parameter_results: list of all ParameterCheck objects
        - out_of_tolerance: list of parameters that failed
        """
        checks: list[ParameterCheck] = []

        # Angle comparisons with 360° wraparound
        checks.append(self._check_angle("gantry_angle", planned.gantry_angle, actual.gantry_angle, tolerance.gantry_angle_tol))
        checks.append(self._check_angle("collimator_angle", planned.collimator_angle, actual.collimator_angle, tolerance.collimator_angle_tol))
        checks.append(self._check_angle("couch_angle", planned.couch_angle, actual.couch_angle, tolerance.couch_angle_tol))

        # Linear position checks (couch)
        checks.append(self._check_value("couch_vertical", planned.couch_vertical, actual.couch_vertical, tolerance.couch_vertical_tol))
        checks.append(self._check_value("couch_lateral", planned.couch_lateral, actual.couch_lateral, tolerance.couch_lateral_tol))
        checks.append(self._check_value("couch_longitudinal", planned.couch_longitudinal, actual.couch_longitudinal, tolerance.couch_longitudinal_tol))

        # Jaw positions
        checks.append(self._check_value("jaw_x1", planned.jaw_x1, actual.jaw_x1, tolerance.jaw_x1_tol))
        checks.append(self._check_value("jaw_x2", planned.jaw_x2, actual.jaw_x2, tolerance.jaw_x2_tol))
        checks.append(self._check_value("jaw_y1", planned.jaw_y1, actual.jaw_y1, tolerance.jaw_y1_tol))
        checks.append(self._check_value("jaw_y2", planned.jaw_y2, actual.jaw_y2, tolerance.jaw_y2_tol))

        # Energy — exact match required
        checks.append(self._check_exact("energy", planned.energy, actual.energy))

        # Dose rate
        checks.append(self._check_value("dose_rate", planned.dose_rate, actual.dose_rate, tolerance.dose_rate_tol))

        # Monitor units
        checks.append(self._check_value("mu", planned.mu, actual.mu, tolerance.mu_tol))

        # MLC leaf positions (per leaf)
        if planned.mlc_positions and actual.mlc_positions and tolerance.mlc_tol is not None:
            if len(planned.mlc_positions) == len(actual.mlc_positions):
                for i, (p, a) in enumerate(zip(planned.mlc_positions, actual.mlc_positions)):
                    checks.append(self._check_value(f"mlc_leaf_{i}", p, a, tolerance.mlc_tol))
            else:
                checks.append(ParameterCheck(
                    name="mlc_positions",
                    planned_value=Decimal(len(planned.mlc_positions)),
                    actual_value=Decimal(len(actual.mlc_positions)),
                    deviation=None,
                    tolerance=None,
                    result="fail",
                ))

        out_of_tol = [c for c in checks if c.result in ("fail", "exact_fail")]

        return VerificationResult(
            overall_result="fail" if out_of_tol else "pass",
            parameter_results=checks,
            out_of_tolerance=out_of_tol,
        )

    def _check_angle(
        self, name: str, planned: Decimal | None, actual: Decimal | None, tolerance: Decimal | None
    ) -> ParameterCheck:
        """Angle comparison with 360-degree wraparound."""
        if planned is None or actual is None:
            return ParameterCheck(name, planned, actual, None, tolerance, "skip")
        if tolerance is None:
            return ParameterCheck(name, planned, actual, None, None, "skip")

        diff = abs(planned - actual)
        # Handle wraparound: e.g., 359.9° vs 0.1° should be 0.2° apart
        diff = min(diff, Decimal("360") - diff)

        result = "pass" if diff <= tolerance else "fail"
        return ParameterCheck(name, planned, actual, diff, tolerance, result)

    def _check_value(
        self, name: str, planned: Decimal | None, actual: Decimal | None, tolerance: Decimal | None
    ) -> ParameterCheck:
        """Numeric value comparison within tolerance."""
        if planned is None or actual is None:
            return ParameterCheck(name, planned, actual, None, tolerance, "skip")
        if tolerance is None:
            return ParameterCheck(name, planned, actual, None, None, "skip")

        diff = abs(planned - actual)
        result = "pass" if diff <= tolerance else "fail"
        return ParameterCheck(name, planned, actual, diff, tolerance, result)

    def _check_exact(
        self, name: str, planned: str | None, actual: str | None
    ) -> ParameterCheck:
        """Exact string match (used for energy, beam mode)."""
        if planned is None or actual is None:
            return ParameterCheck(name, planned, actual, None, None, "skip")

        if planned == actual:
            return ParameterCheck(name, planned, actual, None, None, "exact_match")
        else:
            return ParameterCheck(name, planned, actual, None, None, "exact_fail")

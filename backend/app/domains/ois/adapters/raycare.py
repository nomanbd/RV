"""RaySearch RayCare REST API adapter.

Implements the OIS adapter interface for RayCare, which exposes a modern
REST/JSON API for clinical workflow management. RayCare uses FHIR-aligned
resources internally and provides integration endpoints for treatment
planning (RayStation) and delivery verification.

Reference endpoints follow the RayCare API patterns:
  - /api/v1/patients
  - /api/v1/careplan
  - /api/v1/appointments
  - /api/v1/treatment-deliveries
"""

import time

import httpx

from app.domains.ois.adapters.base import OISAdapter
from app.domains.ois.schemas import (
    OISAppointmentResult,
    OISConnectionTestResult,
    OISPatientResult,
    OISPlanResult,
    OISRecordExportResult,
)


class RayCareAdapter(OISAdapter):
    """Adapter for RaySearch RayCare REST API."""

    def __init__(self, base_url: str, auth_config: dict):
        super().__init__(base_url, auth_config)
        self._token: str | None = None
        self._token_expires_at: float = 0

    async def _authenticate(self, client: httpx.AsyncClient) -> None:
        auth_type = self.auth_config.get("auth_type", "oauth2")

        if auth_type == "oauth2":
            token_url = self.auth_config.get(
                "token_url", f"{self.base_url}/auth/realms/raycare/protocol/openid-connect/token"
            )
            payload = {
                "grant_type": "client_credentials",
                "client_id": self.auth_config["client_id"],
                "client_secret": self.auth_config["client_secret"],
            }
            resp = await client.post(token_url, data=payload)
            resp.raise_for_status()
            data = resp.json()
            self._token = data["access_token"]
            self._token_expires_at = time.time() + data.get("expires_in", 3600) - 60
            client.headers["Authorization"] = f"Bearer {self._token}"

        elif auth_type == "api_key":
            client.headers["X-API-Key"] = self.auth_config["api_key"]

    async def _ensure_auth(self, client: httpx.AsyncClient) -> None:
        if self.auth_config.get("auth_type") == "oauth2" and time.time() >= self._token_expires_at:
            await self._authenticate(client)

    async def test_connection(self) -> OISConnectionTestResult:
        start = time.time()
        try:
            client = await self._get_client()
            await self._ensure_auth(client)
            resp = await client.get("/api/v1/system/health")
            elapsed = (time.time() - start) * 1000

            if resp.status_code == 200:
                data = resp.json()
                return OISConnectionTestResult(
                    success=True,
                    message="Connected to RayCare successfully",
                    response_time_ms=round(elapsed, 1),
                    ois_version=data.get("version", "unknown"),
                    capabilities=[
                        "patients", "care_plans", "appointments",
                        "treatment_deliveries", "fhir",
                    ],
                )
            return OISConnectionTestResult(
                success=False,
                message=f"RayCare responded with status {resp.status_code}",
                response_time_ms=round(elapsed, 1),
            )
        except httpx.ConnectError:
            elapsed = (time.time() - start) * 1000
            return OISConnectionTestResult(
                success=False,
                message="Cannot reach RayCare server - connection refused",
                response_time_ms=round(elapsed, 1),
            )
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return OISConnectionTestResult(
                success=False,
                message=f"Connection failed: {str(e)}",
                response_time_ms=round(elapsed, 1),
            )

    async def search_patients(
        self, mrn: str | None = None, last_name: str | None = None,
        first_name: str | None = None, date_of_birth: str | None = None,
    ) -> list[OISPatientResult]:
        client = await self._get_client()
        await self._ensure_auth(client)

        params = {}
        if mrn:
            params["patientId"] = mrn
        if last_name:
            params["familyName"] = last_name
        if first_name:
            params["givenName"] = first_name
        if date_of_birth:
            params["birthDate"] = date_of_birth

        resp = await client.get("/api/v1/patients", params=params)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for p in data.get("items", data if isinstance(data, list) else []):
            results.append(OISPatientResult(
                external_id=str(p.get("id", "")),
                mrn=p.get("patientId", p.get("identifiers", [{}])[0].get("value", "") if p.get("identifiers") else ""),
                first_name=p.get("givenName", p.get("name", {}).get("given", "")),
                last_name=p.get("familyName", p.get("name", {}).get("family", "")),
                middle_name=p.get("middleName"),
                date_of_birth=p.get("birthDate"),
                sex=self._map_raycare_sex(p.get("gender")),
                diagnoses=self._extract_diagnoses(p),
                courses=self._extract_care_plans(p),
                source_system="raycare",
            ))
        return results

    async def get_patient(self, external_id: str) -> OISPatientResult | None:
        client = await self._get_client()
        await self._ensure_auth(client)

        resp = await client.get(f"/api/v1/patients/{external_id}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        p = resp.json()

        return OISPatientResult(
            external_id=str(p.get("id", "")),
            mrn=p.get("patientId", ""),
            first_name=p.get("givenName", ""),
            last_name=p.get("familyName", ""),
            middle_name=p.get("middleName"),
            date_of_birth=p.get("birthDate"),
            sex=self._map_raycare_sex(p.get("gender")),
            diagnoses=self._extract_diagnoses(p),
            courses=self._extract_care_plans(p),
            source_system="raycare",
        )

    async def get_patient_plans(self, external_patient_id: str) -> list[OISPlanResult]:
        client = await self._get_client()
        await self._ensure_auth(client)

        # RayCare uses CarePlan -> Treatment Planning Order -> Plan
        resp = await client.get(f"/api/v1/patients/{external_patient_id}/careplans")
        resp.raise_for_status()
        data = resp.json()

        plans = []
        for careplan in data.get("items", data if isinstance(data, list) else []):
            careplan_id = careplan.get("id", "")
            # Get plans within each care plan
            plans_resp = await client.get(
                f"/api/v1/patients/{external_patient_id}/careplans/{careplan_id}/plans"
            )
            if plans_resp.status_code != 200:
                continue

            plans_data = plans_resp.json()
            for plan in plans_data.get("items", plans_data if isinstance(plans_data, list) else []):
                plans.append(OISPlanResult(
                    external_id=str(plan.get("id", "")),
                    plan_label=plan.get("name", plan.get("label", "Unknown")),
                    plan_type=plan.get("planType"),
                    status=plan.get("status"),
                    modality=plan.get("modality"),
                    technique=plan.get("technique"),
                    num_beams=plan.get("numberOfBeams", 0),
                    prescribed_dose_cgy=plan.get("prescribedDose"),
                    num_fractions=plan.get("numberOfFractions"),
                    approval_status=plan.get("approvalStatus"),
                    created_date=plan.get("createdAt"),
                    source_system="raycare",
                ))
        return plans

    async def get_plan_details(self, external_patient_id: str, external_plan_id: str) -> dict:
        client = await self._get_client()
        await self._ensure_auth(client)

        resp = await client.get(
            f"/api/v1/patients/{external_patient_id}/plans/{external_plan_id}"
        )
        resp.raise_for_status()
        plan = resp.json()

        # Get beams
        beams_resp = await client.get(
            f"/api/v1/patients/{external_patient_id}/plans/{external_plan_id}/beams"
        )
        beams = []
        if beams_resp.status_code == 200:
            beams = beams_resp.json().get("items", [])

        return {
            "plan": plan,
            "beams": beams,
            "source_system": "raycare",
        }

    async def get_appointments(
        self, date_from: str, date_to: str, machine_name: str | None = None,
    ) -> list[OISAppointmentResult]:
        client = await self._get_client()
        await self._ensure_auth(client)

        params = {
            "fromDate": date_from,
            "toDate": date_to,
        }
        if machine_name:
            params["machineName"] = machine_name

        resp = await client.get("/api/v1/appointments", params=params)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for appt in data.get("items", data if isinstance(data, list) else []):
            patient = appt.get("patient", {})
            results.append(OISAppointmentResult(
                external_id=str(appt.get("id", "")),
                patient_mrn=patient.get("patientId", ""),
                patient_name=f"{patient.get('familyName', '')} {patient.get('givenName', '')}".strip(),
                scheduled_start=appt.get("startTime"),
                scheduled_end=appt.get("endTime"),
                appointment_type=appt.get("type", "treatment"),
                machine_name=appt.get("machine", {}).get("name"),
                status=self._map_raycare_appt_status(appt.get("status")),
                source_system="raycare",
            ))
        return results

    async def export_treatment_record(
        self, external_patient_id: str, session_data: dict,
    ) -> OISRecordExportResult:
        client = await self._get_client()
        await self._ensure_auth(client)

        record_payload = {
            "patientId": external_patient_id,
            "treatmentDate": session_data.get("treatment_date"),
            "machineName": session_data.get("machine_name"),
            "planName": session_data.get("plan_label"),
            "fractionNumber": session_data.get("fraction_number"),
            "deliveredDose": session_data.get("delivered_dose_cgy"),
            "beamDeliveries": [
                {
                    "beamName": beam.get("beam_name"),
                    "deliveredMU": beam.get("delivered_mu"),
                    "gantryAngle": beam.get("gantry_angle"),
                    "collimatorAngle": beam.get("collimator_angle"),
                    "couchAngle": beam.get("couch_angle"),
                    "energy": beam.get("energy"),
                }
                for beam in session_data.get("beams", [])
            ],
        }

        resp = await client.post(
            f"/api/v1/patients/{external_patient_id}/treatment-deliveries",
            json=record_payload,
        )

        if resp.status_code in (200, 201):
            result = resp.json()
            return OISRecordExportResult(
                success=True,
                message="Treatment record exported to RayCare",
                external_record_id=str(result.get("id", "")),
            )
        return OISRecordExportResult(
            success=False,
            message=f"RayCare rejected the record: {resp.status_code} - {resp.text[:200]}",
        )

    @staticmethod
    def _map_raycare_sex(value: str | None) -> str:
        mapping = {"male": "male", "female": "female", "other": "other"}
        return mapping.get((value or "").lower(), "unknown")

    @staticmethod
    def _map_raycare_appt_status(value: str | None) -> str:
        mapping = {
            "scheduled": "scheduled",
            "inProgress": "in_progress",
            "completed": "completed",
            "cancelled": "cancelled",
        }
        return mapping.get(value or "", "scheduled")

    @staticmethod
    def _extract_diagnoses(patient_data: dict) -> list[dict]:
        diagnoses = []
        for d in patient_data.get("diagnoses", []):
            diagnoses.append({
                "code": d.get("code", ""),
                "description": d.get("description", ""),
                "site": d.get("bodySite"),
            })
        return diagnoses

    @staticmethod
    def _extract_care_plans(patient_data: dict) -> list[dict]:
        care_plans = []
        for c in patient_data.get("carePlans", []):
            care_plans.append({
                "id": str(c.get("id", "")),
                "course_id": c.get("name", ""),
                "intent": c.get("intent", ""),
                "start_date": c.get("startDate"),
            })
        return care_plans

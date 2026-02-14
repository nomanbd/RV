"""Varian ARIA Connect REST API adapter.

Implements the OIS adapter interface for Varian Aria using the ARIA Connect
gateway (REST/JSON). Aria exposes patient, course, plan, and scheduling data
through its gateway services.

Reference endpoints follow the ARIA Connect API patterns:
  - /gateway/patients
  - /gateway/courses
  - /gateway/plans
  - /gateway/appointments
  - /gateway/treatmentrecords
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


class AriaAdapter(OISAdapter):
    """Adapter for Varian ARIA Connect REST API."""

    def __init__(self, base_url: str, auth_config: dict):
        super().__init__(base_url, auth_config)
        self._token: str | None = None
        self._token_expires_at: float = 0

    async def _authenticate(self, client: httpx.AsyncClient) -> None:
        auth_type = self.auth_config.get("auth_type", "oauth2")

        if auth_type == "oauth2":
            token_url = self.auth_config.get("token_url", f"{self.base_url}/connect/token")
            payload = {
                "grant_type": "client_credentials",
                "client_id": self.auth_config["client_id"],
                "client_secret": self.auth_config["client_secret"],
                "scope": "aria.gateway",
            }
            resp = await client.post(token_url, data=payload)
            resp.raise_for_status()
            data = resp.json()
            self._token = data["access_token"]
            self._token_expires_at = time.time() + data.get("expires_in", 3600) - 60
            client.headers["Authorization"] = f"Bearer {self._token}"

        elif auth_type == "api_key":
            client.headers["X-API-Key"] = self.auth_config["api_key"]

        elif auth_type == "basic":
            import base64
            creds = base64.b64encode(
                f"{self.auth_config['username']}:{self.auth_config['password']}".encode()
            ).decode()
            client.headers["Authorization"] = f"Basic {creds}"

    async def _ensure_auth(self, client: httpx.AsyncClient) -> None:
        if self.auth_config.get("auth_type") == "oauth2" and time.time() >= self._token_expires_at:
            await self._authenticate(client)

    async def test_connection(self) -> OISConnectionTestResult:
        start = time.time()
        try:
            client = await self._get_client()
            await self._ensure_auth(client)
            resp = await client.get("/gateway/api/version")
            elapsed = (time.time() - start) * 1000

            if resp.status_code == 200:
                data = resp.json()
                return OISConnectionTestResult(
                    success=True,
                    message="Connected to ARIA successfully",
                    response_time_ms=round(elapsed, 1),
                    ois_version=data.get("version", "unknown"),
                    capabilities=["patients", "courses", "plans", "appointments", "treatment_records"],
                )
            return OISConnectionTestResult(
                success=False,
                message=f"ARIA responded with status {resp.status_code}",
                response_time_ms=round(elapsed, 1),
            )
        except httpx.ConnectError:
            elapsed = (time.time() - start) * 1000
            return OISConnectionTestResult(
                success=False,
                message="Cannot reach ARIA server - connection refused",
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
            params["PatientId"] = mrn
        if last_name:
            params["LastName"] = last_name
        if first_name:
            params["FirstName"] = first_name
        if date_of_birth:
            params["DateOfBirth"] = date_of_birth

        resp = await client.get("/gateway/api/patients", params=params)
        resp.raise_for_status()
        patients_data = resp.json()

        results = []
        for p in patients_data.get("Patients", patients_data if isinstance(patients_data, list) else []):
            results.append(OISPatientResult(
                external_id=str(p.get("PatientSer", p.get("PatientId", ""))),
                mrn=p.get("PatientId", p.get("PatientId2", "")),
                first_name=p.get("FirstName", ""),
                last_name=p.get("LastName", ""),
                middle_name=p.get("MiddleName"),
                date_of_birth=p.get("DateOfBirth"),
                sex=self._map_aria_sex(p.get("Sex")),
                diagnoses=self._extract_diagnoses(p),
                courses=self._extract_courses(p),
                source_system="aria",
            ))
        return results

    async def get_patient(self, external_id: str) -> OISPatientResult | None:
        client = await self._get_client()
        await self._ensure_auth(client)

        resp = await client.get(f"/gateway/api/patients/{external_id}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        p = resp.json()

        return OISPatientResult(
            external_id=str(p.get("PatientSer", p.get("PatientId", ""))),
            mrn=p.get("PatientId", ""),
            first_name=p.get("FirstName", ""),
            last_name=p.get("LastName", ""),
            middle_name=p.get("MiddleName"),
            date_of_birth=p.get("DateOfBirth"),
            sex=self._map_aria_sex(p.get("Sex")),
            diagnoses=self._extract_diagnoses(p),
            courses=self._extract_courses(p),
            source_system="aria",
        )

    async def get_patient_plans(self, external_patient_id: str) -> list[OISPlanResult]:
        client = await self._get_client()
        await self._ensure_auth(client)

        # Aria: Get courses first, then plans within each course
        resp = await client.get(f"/gateway/api/patients/{external_patient_id}/courses")
        resp.raise_for_status()
        courses_data = resp.json()

        plans = []
        for course in courses_data.get("Courses", courses_data if isinstance(courses_data, list) else []):
            course_ser = course.get("CourseSer", course.get("CourseId", ""))
            plans_resp = await client.get(
                f"/gateway/api/patients/{external_patient_id}/courses/{course_ser}/plans"
            )
            if plans_resp.status_code != 200:
                continue

            plans_data = plans_resp.json()
            for plan in plans_data.get("PlanSetups", plans_data if isinstance(plans_data, list) else []):
                plans.append(OISPlanResult(
                    external_id=str(plan.get("PlanSetupSer", plan.get("PlanSetupId", ""))),
                    plan_label=plan.get("PlanSetupId", plan.get("PlanLabel", "Unknown")),
                    plan_type=plan.get("PlanType"),
                    status=plan.get("Status"),
                    modality=plan.get("Modality"),
                    technique=plan.get("Technique"),
                    num_beams=len(plan.get("Beams", [])),
                    prescribed_dose_cgy=plan.get("PrescribedDose"),
                    num_fractions=plan.get("NumberOfFractions"),
                    approval_status=plan.get("ApprovalStatus"),
                    created_date=plan.get("CreationDate"),
                    source_system="aria",
                ))
        return plans

    async def get_plan_details(self, external_patient_id: str, external_plan_id: str) -> dict:
        client = await self._get_client()
        await self._ensure_auth(client)

        resp = await client.get(
            f"/gateway/api/patients/{external_patient_id}/plans/{external_plan_id}"
        )
        resp.raise_for_status()
        plan = resp.json()

        # Fetch beam details
        beams_resp = await client.get(
            f"/gateway/api/patients/{external_patient_id}/plans/{external_plan_id}/beams"
        )
        beams = []
        if beams_resp.status_code == 200:
            beams = beams_resp.json().get("Beams", [])

        return {
            "plan": plan,
            "beams": beams,
            "source_system": "aria",
        }

    async def get_appointments(
        self, date_from: str, date_to: str, machine_name: str | None = None,
    ) -> list[OISAppointmentResult]:
        client = await self._get_client()
        await self._ensure_auth(client)

        params = {
            "StartDate": date_from,
            "EndDate": date_to,
        }
        if machine_name:
            params["MachineName"] = machine_name

        resp = await client.get("/gateway/api/appointments", params=params)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for appt in data.get("Appointments", data if isinstance(data, list) else []):
            results.append(OISAppointmentResult(
                external_id=str(appt.get("ScheduledActivitySer", "")),
                patient_mrn=appt.get("PatientId", ""),
                patient_name=f"{appt.get('LastName', '')} {appt.get('FirstName', '')}".strip(),
                scheduled_start=appt.get("ScheduledStartDateTime"),
                scheduled_end=appt.get("ScheduledEndDateTime"),
                appointment_type=appt.get("ActivityCode", "treatment"),
                machine_name=appt.get("MachineName"),
                status=self._map_aria_appt_status(appt.get("Status")),
                source_system="aria",
            ))
        return results

    async def export_treatment_record(
        self, external_patient_id: str, session_data: dict,
    ) -> OISRecordExportResult:
        client = await self._get_client()
        await self._ensure_auth(client)

        # Map session data to ARIA treatment record format
        record_payload = {
            "PatientId": external_patient_id,
            "TreatmentDate": session_data.get("treatment_date"),
            "MachineName": session_data.get("machine_name"),
            "PlanSetupId": session_data.get("plan_label"),
            "FractionNumber": session_data.get("fraction_number"),
            "DeliveredDose": session_data.get("delivered_dose_cgy"),
            "Beams": [
                {
                    "BeamId": beam.get("beam_name"),
                    "DeliveredMU": beam.get("delivered_mu"),
                    "GantryAngle": beam.get("gantry_angle"),
                    "CollimatorAngle": beam.get("collimator_angle"),
                    "CouchAngle": beam.get("couch_angle"),
                    "Energy": beam.get("energy"),
                }
                for beam in session_data.get("beams", [])
            ],
        }

        resp = await client.post(
            f"/gateway/api/patients/{external_patient_id}/treatmentrecords",
            json=record_payload,
        )

        if resp.status_code in (200, 201):
            result = resp.json()
            return OISRecordExportResult(
                success=True,
                message="Treatment record exported to ARIA",
                external_record_id=str(result.get("TreatmentRecordSer", "")),
            )
        return OISRecordExportResult(
            success=False,
            message=f"ARIA rejected the record: {resp.status_code} - {resp.text[:200]}",
        )

    @staticmethod
    def _map_aria_sex(value: str | None) -> str:
        mapping = {"Male": "male", "Female": "female", "Other": "other"}
        return mapping.get(value or "", "unknown")

    @staticmethod
    def _map_aria_appt_status(value: str | None) -> str:
        mapping = {
            "Open": "scheduled",
            "InProgress": "in_progress",
            "Completed": "completed",
            "Cancelled": "cancelled",
        }
        return mapping.get(value or "", "scheduled")

    @staticmethod
    def _extract_diagnoses(patient_data: dict) -> list[dict]:
        diagnoses = []
        for d in patient_data.get("Diagnoses", []):
            diagnoses.append({
                "code": d.get("DiagnosisCode", ""),
                "description": d.get("Description", ""),
                "site": d.get("BodySite"),
            })
        return diagnoses

    @staticmethod
    def _extract_courses(patient_data: dict) -> list[dict]:
        courses = []
        for c in patient_data.get("Courses", []):
            courses.append({
                "id": str(c.get("CourseSer", "")),
                "course_id": c.get("CourseId", ""),
                "intent": c.get("Intent", ""),
                "start_date": c.get("StartDateTime"),
            })
        return courses

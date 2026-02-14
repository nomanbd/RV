"""HL7 FHIR R4 adapter for generic OIS interoperability.

Provides FHIR-based integration that works with any FHIR-compliant OIS.
Supports standard FHIR resources:
  - Patient (demographics, identifiers)
  - Condition (diagnoses)
  - CarePlan (treatment courses)
  - Appointment (scheduling)
  - Procedure (treatment records)
  - Device (treatment machines)

Can be used standalone or as a supplement to Aria/RayCare adapters
when those systems expose FHIR endpoints.
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


class FHIRAdapter(OISAdapter):
    """HL7 FHIR R4 adapter for standards-based OIS integration."""

    def __init__(self, base_url: str, auth_config: dict):
        super().__init__(base_url, auth_config)
        self._token: str | None = None
        self._token_expires_at: float = 0

    async def _authenticate(self, client: httpx.AsyncClient) -> None:
        auth_type = self.auth_config.get("auth_type", "oauth2")
        client.headers["Accept"] = "application/fhir+json"
        client.headers["Content-Type"] = "application/fhir+json"

        if auth_type == "oauth2":
            # SMART on FHIR authorization
            token_url = self.auth_config.get("token_url", f"{self.base_url}/auth/token")
            payload = {
                "grant_type": "client_credentials",
                "client_id": self.auth_config["client_id"],
                "client_secret": self.auth_config["client_secret"],
                "scope": "system/*.read system/*.write",
            }
            resp = await client.post(token_url, data=payload)
            resp.raise_for_status()
            data = resp.json()
            self._token = data["access_token"]
            self._token_expires_at = time.time() + data.get("expires_in", 3600) - 60
            client.headers["Authorization"] = f"Bearer {self._token}"

        elif auth_type == "basic":
            import base64
            creds = base64.b64encode(
                f"{self.auth_config['username']}:{self.auth_config['password']}".encode()
            ).decode()
            client.headers["Authorization"] = f"Basic {creds}"

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
            # FHIR capability statement
            resp = await client.get("/metadata")
            elapsed = (time.time() - start) * 1000

            if resp.status_code == 200:
                data = resp.json()
                resource_types = []
                for rest in data.get("rest", []):
                    for resource in rest.get("resource", []):
                        resource_types.append(resource.get("type", ""))
                capabilities = []
                if "Patient" in resource_types:
                    capabilities.append("patients")
                if "CarePlan" in resource_types:
                    capabilities.append("care_plans")
                if "Appointment" in resource_types:
                    capabilities.append("appointments")
                if "Procedure" in resource_types:
                    capabilities.append("treatment_records")

                return OISConnectionTestResult(
                    success=True,
                    message="Connected to FHIR server successfully",
                    response_time_ms=round(elapsed, 1),
                    ois_version=data.get("fhirVersion", "R4"),
                    capabilities=capabilities,
                )
            return OISConnectionTestResult(
                success=False,
                message=f"FHIR server responded with status {resp.status_code}",
                response_time_ms=round(elapsed, 1),
            )
        except httpx.ConnectError:
            elapsed = (time.time() - start) * 1000
            return OISConnectionTestResult(
                success=False,
                message="Cannot reach FHIR server - connection refused",
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

        params: dict[str, str] = {"_count": "50"}
        if mrn:
            params["identifier"] = mrn
        if last_name:
            params["family"] = last_name
        if first_name:
            params["given"] = first_name
        if date_of_birth:
            params["birthdate"] = date_of_birth

        resp = await client.get("/Patient", params=params)
        resp.raise_for_status()
        bundle = resp.json()

        results = []
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") != "Patient":
                continue
            results.append(self._fhir_patient_to_result(resource))
        return results

    async def get_patient(self, external_id: str) -> OISPatientResult | None:
        client = await self._get_client()
        await self._ensure_auth(client)

        resp = await client.get(f"/Patient/{external_id}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        resource = resp.json()
        return self._fhir_patient_to_result(resource)

    async def get_patient_plans(self, external_patient_id: str) -> list[OISPlanResult]:
        client = await self._get_client()
        await self._ensure_auth(client)

        # Search CarePlan resources for radiation therapy
        resp = await client.get(
            "/CarePlan",
            params={
                "subject": f"Patient/{external_patient_id}",
                "category": "radiation-therapy",
                "_count": "50",
            },
        )
        resp.raise_for_status()
        bundle = resp.json()

        plans = []
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") != "CarePlan":
                continue
            plans.append(OISPlanResult(
                external_id=resource.get("id", ""),
                plan_label=resource.get("title", "Unknown"),
                plan_type=self._get_fhir_extension(resource, "plan-type"),
                status=resource.get("status"),
                modality=self._get_fhir_extension(resource, "modality"),
                technique=self._get_fhir_extension(resource, "technique"),
                num_beams=int(self._get_fhir_extension(resource, "number-of-beams") or 0),
                prescribed_dose_cgy=self._parse_float(self._get_fhir_extension(resource, "prescribed-dose")),
                num_fractions=self._parse_int(self._get_fhir_extension(resource, "number-of-fractions")),
                approval_status=self._get_fhir_extension(resource, "approval-status"),
                created_date=resource.get("created"),
                source_system="fhir",
            ))
        return plans

    async def get_plan_details(self, external_patient_id: str, external_plan_id: str) -> dict:
        client = await self._get_client()
        await self._ensure_auth(client)

        resp = await client.get(f"/CarePlan/{external_plan_id}")
        resp.raise_for_status()
        plan = resp.json()

        return {
            "plan": plan,
            "beams": [],
            "source_system": "fhir",
        }

    async def get_appointments(
        self, date_from: str, date_to: str, machine_name: str | None = None,
    ) -> list[OISAppointmentResult]:
        client = await self._get_client()
        await self._ensure_auth(client)

        params: dict[str, str] = {
            "date": f"ge{date_from}",
            "_count": "100",
            "service-type": "radiation-therapy",
        }

        resp = await client.get("/Appointment", params=params)
        resp.raise_for_status()
        bundle = resp.json()

        results = []
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") != "Appointment":
                continue

            patient_ref = ""
            patient_name = ""
            for participant in resource.get("participant", []):
                actor = participant.get("actor", {})
                if "Patient/" in actor.get("reference", ""):
                    patient_ref = actor.get("reference", "").split("/")[-1]
                    patient_name = actor.get("display", "")

            results.append(OISAppointmentResult(
                external_id=resource.get("id", ""),
                patient_mrn=patient_ref,
                patient_name=patient_name,
                scheduled_start=resource.get("start"),
                scheduled_end=resource.get("end"),
                appointment_type=resource.get("serviceType", [{}])[0].get("text", "treatment")
                    if resource.get("serviceType") else "treatment",
                machine_name=self._get_fhir_extension(resource, "machine-name"),
                status=self._map_fhir_appt_status(resource.get("status")),
                source_system="fhir",
            ))
        return results

    async def export_treatment_record(
        self, external_patient_id: str, session_data: dict,
    ) -> OISRecordExportResult:
        client = await self._get_client()
        await self._ensure_auth(client)

        # Create a Procedure resource for the treatment delivery
        procedure = {
            "resourceType": "Procedure",
            "status": "completed",
            "category": {
                "coding": [{"system": "http://snomed.info/sct", "code": "108290001", "display": "Radiation therapy"}]
            },
            "subject": {"reference": f"Patient/{external_patient_id}"},
            "performedDateTime": session_data.get("treatment_date"),
            "extension": [
                {
                    "url": "http://hl7.org/fhir/us/mcode/StructureDefinition/delivered-dose",
                    "valueQuantity": {
                        "value": session_data.get("delivered_dose_cgy"),
                        "unit": "cGy",
                    },
                },
                {
                    "url": "http://hl7.org/fhir/us/mcode/StructureDefinition/fraction-number",
                    "valueInteger": session_data.get("fraction_number"),
                },
            ],
        }

        resp = await client.post("/Procedure", json=procedure)
        if resp.status_code in (200, 201):
            result = resp.json()
            return OISRecordExportResult(
                success=True,
                message="Treatment record exported via FHIR",
                external_record_id=result.get("id", ""),
            )
        return OISRecordExportResult(
            success=False,
            message=f"FHIR server rejected the record: {resp.status_code}",
        )

    def _fhir_patient_to_result(self, resource: dict) -> OISPatientResult:
        # Extract MRN from identifiers
        mrn = ""
        for ident in resource.get("identifier", []):
            if ident.get("type", {}).get("coding", [{}])[0].get("code") == "MR":
                mrn = ident.get("value", "")
                break
        if not mrn and resource.get("identifier"):
            mrn = resource["identifier"][0].get("value", "")

        # Extract name
        names = resource.get("name", [{}])
        official_name = names[0]
        for n in names:
            if n.get("use") == "official":
                official_name = n
                break

        given = official_name.get("given", [])
        return OISPatientResult(
            external_id=resource.get("id", ""),
            mrn=mrn,
            first_name=given[0] if given else "",
            last_name=official_name.get("family", ""),
            middle_name=given[1] if len(given) > 1 else None,
            date_of_birth=resource.get("birthDate"),
            sex=resource.get("gender", "unknown"),
            diagnoses=[],
            courses=[],
            source_system="fhir",
        )

    @staticmethod
    def _get_fhir_extension(resource: dict, name: str) -> str | None:
        for ext in resource.get("extension", []):
            if name in ext.get("url", ""):
                for key in ("valueString", "valueInteger", "valueDecimal", "valueCode"):
                    if key in ext:
                        return str(ext[key])
        return None

    @staticmethod
    def _map_fhir_appt_status(value: str | None) -> str:
        mapping = {
            "booked": "scheduled",
            "arrived": "in_progress",
            "fulfilled": "completed",
            "cancelled": "cancelled",
            "noshow": "no_show",
        }
        return mapping.get(value or "", "scheduled")

    @staticmethod
    def _parse_float(val: str | None) -> float | None:
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_int(val: str | None) -> int | None:
        if val is None:
            return None
        try:
            return int(val)
        except (ValueError, TypeError):
            return None

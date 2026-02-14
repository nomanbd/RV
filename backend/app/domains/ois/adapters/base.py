"""Abstract base adapter defining the interface for all OIS integrations."""

from abc import ABC, abstractmethod

import httpx

from app.domains.ois.schemas import (
    OISAppointmentResult,
    OISConnectionTestResult,
    OISPatientResult,
    OISPlanResult,
    OISRecordExportResult,
)


class OISAdapter(ABC):
    """Base adapter interface for Oncology Information System integrations.

    Each concrete adapter (Aria, RayCare, generic FHIR) implements this interface
    to provide uniform access to OIS capabilities.
    """

    def __init__(self, base_url: str, auth_config: dict):
        self.base_url = base_url.rstrip("/")
        self.auth_config = auth_config
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(30.0, connect=10.0),
                verify=self.auth_config.get("verify_ssl", True),
            )
            await self._authenticate(self._client)
        return self._client

    @abstractmethod
    async def _authenticate(self, client: httpx.AsyncClient) -> None:
        """Perform authentication (OAuth2, API key, basic, certificate)."""
        ...

    @abstractmethod
    async def test_connection(self) -> OISConnectionTestResult:
        """Test connectivity and return system info."""
        ...

    @abstractmethod
    async def search_patients(
        self, mrn: str | None = None, last_name: str | None = None,
        first_name: str | None = None, date_of_birth: str | None = None,
    ) -> list[OISPatientResult]:
        """Search for patients in the OIS."""
        ...

    @abstractmethod
    async def get_patient(self, external_id: str) -> OISPatientResult | None:
        """Get a specific patient by their OIS identifier."""
        ...

    @abstractmethod
    async def get_patient_plans(self, external_patient_id: str) -> list[OISPlanResult]:
        """Get treatment plans for a patient."""
        ...

    @abstractmethod
    async def get_plan_details(self, external_patient_id: str, external_plan_id: str) -> dict:
        """Get full plan details including beam data for import."""
        ...

    @abstractmethod
    async def get_appointments(
        self, date_from: str, date_to: str, machine_name: str | None = None,
    ) -> list[OISAppointmentResult]:
        """Get scheduled appointments."""
        ...

    @abstractmethod
    async def export_treatment_record(
        self, external_patient_id: str, session_data: dict,
    ) -> OISRecordExportResult:
        """Push a completed treatment session record back to the OIS."""
        ...

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

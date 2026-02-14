"""
DICOM SCP (Service Class Provider) Server.

Listens for incoming DICOM associations and handles:
- C-STORE: Receive and store RT Plan, RT Dose, RT Struct, RT Image, CT
- C-FIND: Query patient/study/series information
- C-ECHO: Verification (ping)
"""

import logging
import threading
from typing import Any

from pynetdicom import AE, evt
from pynetdicom.sop_class import (
    CTImageStorage,
    DigitalXRayImageStorageForPresentation,
    PatientRootQueryRetrieveInformationModelFind,
    PatientRootQueryRetrieveInformationModelGet,
    PatientRootQueryRetrieveInformationModelMove,
    RTBeamsTreatmentRecordStorage,
    RTDoseStorage,
    RTImageStorage,
    RTPlanStorage,
    RTStructureSetStorage,
    Verification,
)

from app.core.config import settings

logger = logging.getLogger(__name__)

# SOP Classes we accept
STORAGE_SOP_CLASSES = [
    RTPlanStorage,
    RTDoseStorage,
    RTStructureSetStorage,
    RTBeamsTreatmentRecordStorage,
    RTImageStorage,
    CTImageStorage,
    DigitalXRayImageStorageForPresentation,
]

QR_SOP_CLASSES = [
    PatientRootQueryRetrieveInformationModelFind,
    PatientRootQueryRetrieveInformationModelMove,
    PatientRootQueryRetrieveInformationModelGet,
]


class DicomSCP:
    """DICOM SCP server for receiving RT objects."""

    def __init__(self, ae_title: str | None = None, port: int | None = None):
        self.ae_title = ae_title or settings.DICOM_AE_TITLE
        self.port = port or settings.DICOM_SCP_PORT
        self.ae: AE | None = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._store_handler: Any = None

    def set_store_handler(self, handler):
        """Set a callback for C-STORE events: handler(ds, context) -> int status."""
        self._store_handler = handler

    def start(self) -> None:
        """Start the SCP in a background thread."""
        if self._running:
            logger.warning("DICOM SCP already running")
            return

        self.ae = AE(ae_title=self.ae_title)

        # Add supported presentation contexts
        for sop_class in STORAGE_SOP_CLASSES:
            self.ae.add_supported_context(sop_class)
        for sop_class in QR_SOP_CLASSES:
            self.ae.add_supported_context(sop_class)
        self.ae.add_supported_context(Verification)

        # Event handlers
        handlers = [
            (evt.EVT_C_STORE, self._handle_c_store),
            (evt.EVT_C_ECHO, self._handle_c_echo),
            (evt.EVT_C_FIND, self._handle_c_find),
        ]

        self._running = True
        self._thread = threading.Thread(
            target=self._run_server,
            args=(handlers,),
            daemon=True,
            name="dicom-scp",
        )
        self._thread.start()
        logger.info(f"DICOM SCP started on port {self.port} (AE: {self.ae_title})")

    def _run_server(self, handlers):
        """Run the SCP server (blocking, called in thread)."""
        try:
            self.ae.start_server(
                ("0.0.0.0", self.port),
                evt_handlers=handlers,
                block=True,
            )
        except Exception as e:
            logger.error(f"DICOM SCP error: {e}")
            self._running = False

    def stop(self) -> None:
        """Stop the SCP server."""
        if self.ae and self._running:
            self.ae.shutdown()
            self._running = False
            if self._thread:
                self._thread.join(timeout=5)
            logger.info("DICOM SCP stopped")

    @property
    def is_running(self) -> bool:
        return self._running

    def _handle_c_store(self, event):
        """Handle incoming C-STORE requests."""
        ds = event.dataset
        ds.file_meta = event.file_meta

        sop_class_uid = str(ds.SOPClassUID)
        sop_instance_uid = str(ds.SOPInstanceUID)
        patient_id = str(getattr(ds, "PatientID", "unknown"))

        logger.info(
            f"C-STORE received: SOP Class={sop_class_uid}, "
            f"SOP Instance={sop_instance_uid}, Patient={patient_id}"
        )

        try:
            if self._store_handler:
                return self._store_handler(ds, event.context)

            # Default: store to filesystem
            from app.dicom.storage.file_manager import DicomFileManager

            fm = DicomFileManager()
            path = fm.store(ds)
            logger.info(f"Stored DICOM file: {path}")
            return 0x0000  # Success
        except Exception as e:
            logger.error(f"C-STORE failed: {e}")
            return 0xC000  # Error

    def _handle_c_echo(self, event):
        """Handle C-ECHO (verification) requests."""
        logger.info("C-ECHO received")
        return 0x0000  # Success

    def _handle_c_find(self, event):
        """Handle C-FIND queries."""
        ds = event.identifier
        logger.info(f"C-FIND received: {ds}")

        # Return empty for now — will be connected to DB in Phase 8
        yield 0xFF00, None  # Pending (no matches)

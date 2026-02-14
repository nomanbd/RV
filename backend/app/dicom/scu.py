"""
DICOM SCU (Service Class User) Client.

Connects to remote DICOM peers (PACS, TPS) for:
- C-STORE: Send DICOM objects to remote systems
- C-FIND: Query remote systems for patients/studies
- C-MOVE: Request retrieval from remote systems
- C-ECHO: Verify connectivity to remote peers
"""

import logging
from dataclasses import dataclass

import pydicom
from pynetdicom import AE
from pynetdicom.sop_class import (
    CTImageStorage,
    PatientRootQueryRetrieveInformationModelFind,
    PatientRootQueryRetrieveInformationModelMove,
    RTDoseStorage,
    RTImageStorage,
    RTPlanStorage,
    RTStructureSetStorage,
    Verification,
)

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class DicomPeer:
    """Remote DICOM peer configuration."""

    ae_title: str
    host: str
    port: int
    description: str = ""


class DicomSCU:
    """DICOM SCU client for sending/querying remote systems."""

    def __init__(self, ae_title: str | None = None):
        self.ae_title = ae_title or settings.DICOM_AE_TITLE

    def echo(self, peer: DicomPeer) -> bool:
        """Send C-ECHO to verify connectivity with a remote peer.

        Returns True if the peer responds successfully.
        """
        ae = AE(ae_title=self.ae_title)
        ae.add_requested_context(Verification)

        try:
            assoc = ae.associate(peer.host, peer.port, ae_title=peer.ae_title)
            if assoc.is_established:
                status = assoc.send_c_echo()
                assoc.release()
                if status and status.Status == 0x0000:
                    logger.info(f"C-ECHO success: {peer.ae_title}@{peer.host}:{peer.port}")
                    return True
            logger.warning(f"C-ECHO failed: {peer.ae_title}@{peer.host}:{peer.port}")
            return False
        except Exception as e:
            logger.error(f"C-ECHO error to {peer.ae_title}: {e}")
            return False

    def send(self, peer: DicomPeer, filepath: str) -> bool:
        """Send a DICOM file to a remote peer via C-STORE.

        Args:
            peer: Remote DICOM peer configuration
            filepath: Path to the DICOM file to send

        Returns True if the file was sent successfully.
        """
        ae = AE(ae_title=self.ae_title)
        # Add all storage SOP classes
        for sop in [RTPlanStorage, RTDoseStorage, RTStructureSetStorage, RTImageStorage, CTImageStorage]:
            ae.add_requested_context(sop)

        try:
            ds = pydicom.dcmread(filepath)
            assoc = ae.associate(peer.host, peer.port, ae_title=peer.ae_title)
            if assoc.is_established:
                status = assoc.send_c_store(ds)
                assoc.release()
                if status and status.Status == 0x0000:
                    logger.info(f"C-STORE success to {peer.ae_title}: {filepath}")
                    return True
            logger.warning(f"C-STORE failed to {peer.ae_title}: {filepath}")
            return False
        except Exception as e:
            logger.error(f"C-STORE error: {e}")
            return False

    def query_patients(self, peer: DicomPeer, patient_name: str = "", patient_id: str = "") -> list[dict]:
        """Query remote peer for patients via C-FIND at PATIENT level.

        Returns list of matching patient records.
        """
        ae = AE(ae_title=self.ae_title)
        ae.add_requested_context(PatientRootQueryRetrieveInformationModelFind)

        ds = pydicom.Dataset()
        ds.QueryRetrieveLevel = "PATIENT"
        ds.PatientName = patient_name or "*"
        ds.PatientID = patient_id or "*"
        ds.PatientBirthDate = ""
        ds.PatientSex = ""

        results = []
        try:
            assoc = ae.associate(peer.host, peer.port, ae_title=peer.ae_title)
            if assoc.is_established:
                responses = assoc.send_c_find(ds, PatientRootQueryRetrieveInformationModelFind)
                for status, identifier in responses:
                    if status and status.Status in (0xFF00, 0xFF01) and identifier:
                        results.append({
                            "patient_name": str(getattr(identifier, "PatientName", "")),
                            "patient_id": str(getattr(identifier, "PatientID", "")),
                            "birth_date": str(getattr(identifier, "PatientBirthDate", "")),
                            "sex": str(getattr(identifier, "PatientSex", "")),
                        })
                assoc.release()
        except Exception as e:
            logger.error(f"C-FIND error: {e}")

        return results

    def query_studies(self, peer: DicomPeer, patient_id: str) -> list[dict]:
        """Query remote peer for studies of a specific patient."""
        ae = AE(ae_title=self.ae_title)
        ae.add_requested_context(PatientRootQueryRetrieveInformationModelFind)

        ds = pydicom.Dataset()
        ds.QueryRetrieveLevel = "STUDY"
        ds.PatientID = patient_id
        ds.StudyInstanceUID = ""
        ds.StudyDate = ""
        ds.StudyDescription = ""
        ds.Modality = ""

        results = []
        try:
            assoc = ae.associate(peer.host, peer.port, ae_title=peer.ae_title)
            if assoc.is_established:
                responses = assoc.send_c_find(ds, PatientRootQueryRetrieveInformationModelFind)
                for status, identifier in responses:
                    if status and status.Status in (0xFF00, 0xFF01) and identifier:
                        results.append({
                            "study_instance_uid": str(getattr(identifier, "StudyInstanceUID", "")),
                            "study_date": str(getattr(identifier, "StudyDate", "")),
                            "study_description": str(getattr(identifier, "StudyDescription", "")),
                            "modality": str(getattr(identifier, "Modality", "")),
                        })
                assoc.release()
        except Exception as e:
            logger.error(f"C-FIND studies error: {e}")

        return results

    def retrieve(self, peer: DicomPeer, study_uid: str, move_destination: str | None = None) -> bool:
        """Request C-MOVE retrieval of a study from a remote peer.

        The remote peer will send the objects to our SCP (or to move_destination).
        """
        ae = AE(ae_title=self.ae_title)
        ae.add_requested_context(PatientRootQueryRetrieveInformationModelMove)

        ds = pydicom.Dataset()
        ds.QueryRetrieveLevel = "STUDY"
        ds.StudyInstanceUID = study_uid

        dest = move_destination or self.ae_title

        try:
            assoc = ae.associate(peer.host, peer.port, ae_title=peer.ae_title)
            if assoc.is_established:
                responses = assoc.send_c_move(ds, dest, PatientRootQueryRetrieveInformationModelMove)
                for status, identifier in responses:
                    if status and status.Status == 0x0000:
                        logger.info(f"C-MOVE complete for study {study_uid}")
                        assoc.release()
                        return True
                assoc.release()
        except Exception as e:
            logger.error(f"C-MOVE error: {e}")

        return False

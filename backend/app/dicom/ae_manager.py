"""
DICOM Application Entity Lifecycle Manager.

Manages the DICOM SCP server lifecycle alongside the FastAPI application.
Provides start/stop control and status reporting via API.
"""

import logging

from app.dicom.scp import DicomSCP
from app.dicom.scu import DicomSCU, DicomPeer

logger = logging.getLogger(__name__)


class AEManager:
    """Singleton manager for DICOM Application Entity services."""

    _instance: "AEManager | None" = None
    _scp: DicomSCP | None = None
    _scu: DicomSCU | None = None
    _peers: dict[str, DicomPeer] = {}

    @classmethod
    def get_instance(cls) -> "AEManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def start_scp(self) -> bool:
        """Start the DICOM SCP server."""
        if self._scp and self._scp.is_running:
            return True
        self._scp = DicomSCP()
        self._scp.start()
        return self._scp.is_running

    def stop_scp(self) -> None:
        """Stop the DICOM SCP server."""
        if self._scp:
            self._scp.stop()

    @property
    def scp_running(self) -> bool:
        return self._scp.is_running if self._scp else False

    def get_scu(self) -> DicomSCU:
        """Get or create the DICOM SCU client."""
        if self._scu is None:
            self._scu = DicomSCU()
        return self._scu

    def add_peer(self, name: str, ae_title: str, host: str, port: int, description: str = "") -> DicomPeer:
        """Register a remote DICOM peer."""
        peer = DicomPeer(ae_title=ae_title, host=host, port=port, description=description)
        self._peers[name] = peer
        logger.info(f"Added DICOM peer: {name} ({ae_title}@{host}:{port})")
        return peer

    def remove_peer(self, name: str) -> bool:
        """Remove a registered DICOM peer."""
        if name in self._peers:
            del self._peers[name]
            return True
        return False

    def get_peer(self, name: str) -> DicomPeer | None:
        """Get a registered DICOM peer by name."""
        return self._peers.get(name)

    def list_peers(self) -> dict[str, DicomPeer]:
        """List all registered DICOM peers."""
        return dict(self._peers)

    def echo_peer(self, name: str) -> bool:
        """Test connectivity to a registered peer via C-ECHO."""
        peer = self._peers.get(name)
        if not peer:
            return False
        scu = self.get_scu()
        return scu.echo(peer)

    def get_status(self) -> dict:
        """Get the current status of DICOM services."""
        return {
            "scp_running": self.scp_running,
            "scp_ae_title": self._scp.ae_title if self._scp else None,
            "scp_port": self._scp.port if self._scp else None,
            "registered_peers": len(self._peers),
            "peer_names": list(self._peers.keys()),
        }

"""DICOM network services API endpoints."""

import uuid

from fastapi import APIRouter, Depends, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.dicom.ae_manager import AEManager
from app.domains.auth.models import User

router = APIRouter(prefix="/dicom", tags=["dicom"])


class PeerCreate(BaseModel):
    name: str = Field(max_length=100)
    ae_title: str = Field(max_length=16)
    host: str = Field(max_length=255)
    port: int = Field(ge=1, le=65535)
    description: str = ""


class PeerResponse(BaseModel):
    name: str
    ae_title: str
    host: str
    port: int
    description: str


class DicomStatusResponse(BaseModel):
    scp_running: bool
    scp_ae_title: str | None
    scp_port: int | None
    registered_peers: int
    peer_names: list[str]


class EchoResponse(BaseModel):
    peer_name: str
    success: bool


# --- SCP Control ---


@router.get("/status", response_model=DicomStatusResponse)
async def get_dicom_status(
    current_user: User = Depends(get_current_user),
):
    mgr = AEManager.get_instance()
    return mgr.get_status()


@router.post("/scp/start")
async def start_scp(
    current_user: User = Depends(get_current_user),
):
    mgr = AEManager.get_instance()
    started = mgr.start_scp()
    return {"started": started, "status": mgr.get_status()}


@router.post("/scp/stop")
async def stop_scp(
    current_user: User = Depends(get_current_user),
):
    mgr = AEManager.get_instance()
    mgr.stop_scp()
    return {"stopped": True, "status": mgr.get_status()}


# --- Peer Management ---


@router.get("/peers", response_model=list[PeerResponse])
async def list_peers(
    current_user: User = Depends(get_current_user),
):
    mgr = AEManager.get_instance()
    peers = mgr.list_peers()
    return [
        PeerResponse(
            name=name,
            ae_title=peer.ae_title,
            host=peer.host,
            port=peer.port,
            description=peer.description,
        )
        for name, peer in peers.items()
    ]


@router.post("/peers", response_model=PeerResponse, status_code=201)
async def add_peer(
    data: PeerCreate,
    current_user: User = Depends(get_current_user),
):
    mgr = AEManager.get_instance()
    peer = mgr.add_peer(
        name=data.name,
        ae_title=data.ae_title,
        host=data.host,
        port=data.port,
        description=data.description,
    )
    return PeerResponse(
        name=data.name,
        ae_title=peer.ae_title,
        host=peer.host,
        port=peer.port,
        description=peer.description,
    )


@router.delete("/peers/{peer_name}")
async def remove_peer(
    peer_name: str,
    current_user: User = Depends(get_current_user),
):
    mgr = AEManager.get_instance()
    removed = mgr.remove_peer(peer_name)
    return {"removed": removed}


@router.post("/peers/{peer_name}/echo", response_model=EchoResponse)
async def echo_peer(
    peer_name: str,
    current_user: User = Depends(get_current_user),
):
    mgr = AEManager.get_instance()
    success = mgr.echo_peer(peer_name)
    return EchoResponse(peer_name=peer_name, success=success)

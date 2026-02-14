import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.domains.auth.models import User
from app.domains.machines.schemas import (
    MachineCreate,
    MachineResponse,
    MachineUpdate,
    ToleranceTableCreate,
    ToleranceTableResponse,
    ToleranceTableUpdate,
)
from app.domains.machines.service import MachineService

router = APIRouter(prefix="/machines", tags=["machines"])


class MachineStatusUpdate(BaseModel):
    status: str = Field(pattern="^(active|maintenance|decommissioned)$")


# --- Machines ---

@router.get("", response_model=list[MachineResponse])
async def list_machines(
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MachineService(db)
    return await service.list_machines(status=status)


@router.post("", response_model=MachineResponse, status_code=201)
async def create_machine(
    data: MachineCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MachineService(db)
    return await service.create_machine(data)


@router.get("/{machine_id}", response_model=MachineResponse)
async def get_machine(
    machine_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MachineService(db)
    return await service.get_machine(machine_id)


@router.put("/{machine_id}", response_model=MachineResponse)
async def update_machine(
    machine_id: uuid.UUID,
    data: MachineUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MachineService(db)
    return await service.update_machine(machine_id, data)


@router.patch("/{machine_id}/status", response_model=MachineResponse)
async def update_machine_status(
    machine_id: uuid.UUID,
    data: MachineStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MachineService(db)
    return await service.update_status(machine_id, data.status)


@router.get("/{machine_id}/tolerances", response_model=list[ToleranceTableResponse])
async def list_machine_tolerances(
    machine_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MachineService(db)
    return await service.list_tolerances(machine_id=machine_id)


# --- Tolerance Tables (top-level) ---

tolerances_router = APIRouter(tags=["machines"])


@tolerances_router.post("/tolerances", response_model=ToleranceTableResponse, status_code=201)
async def create_tolerance(
    data: ToleranceTableCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MachineService(db)
    return await service.create_tolerance(data)


@tolerances_router.get("/tolerances/{tolerance_id}", response_model=ToleranceTableResponse)
async def get_tolerance(
    tolerance_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MachineService(db)
    return await service.get_tolerance(tolerance_id)


@tolerances_router.put("/tolerances/{tolerance_id}", response_model=ToleranceTableResponse)
async def update_tolerance(
    tolerance_id: uuid.UUID,
    data: ToleranceTableUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MachineService(db)
    return await service.update_tolerance(tolerance_id, data)

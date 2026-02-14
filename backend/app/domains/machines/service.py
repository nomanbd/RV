import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.domains.machines.models import ToleranceTable, TreatmentMachine
from app.domains.machines.schemas import (
    MachineCreate,
    MachineUpdate,
    ToleranceTableCreate,
    ToleranceTableUpdate,
)


class MachineService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Treatment Machines ---

    async def create_machine(self, data: MachineCreate) -> TreatmentMachine:
        # Check name uniqueness
        existing = await self.db.execute(
            select(TreatmentMachine).where(TreatmentMachine.name == data.name)
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"Machine with name '{data.name}' already exists")

        machine = TreatmentMachine(**data.model_dump())
        self.db.add(machine)
        await self.db.flush()
        return machine

    async def get_machine(self, machine_id: uuid.UUID) -> TreatmentMachine:
        result = await self.db.execute(
            select(TreatmentMachine).where(TreatmentMachine.id == machine_id)
        )
        machine = result.scalar_one_or_none()
        if machine is None:
            raise NotFoundError("Treatment machine not found")
        return machine

    async def list_machines(self, status: str | None = None) -> list[TreatmentMachine]:
        query = select(TreatmentMachine)
        if status is not None:
            query = query.where(TreatmentMachine.status == status)
        query = query.order_by(TreatmentMachine.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_machine(self, machine_id: uuid.UUID, data: MachineUpdate) -> TreatmentMachine:
        machine = await self.get_machine(machine_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(machine, field, value)
        await self.db.flush()
        return machine

    async def update_status(self, machine_id: uuid.UUID, status: str) -> TreatmentMachine:
        machine = await self.get_machine(machine_id)
        machine.status = status
        await self.db.flush()
        return machine

    # --- Tolerance Tables ---

    async def create_tolerance(self, data: ToleranceTableCreate) -> ToleranceTable:
        # Validate machine_id if provided
        if data.machine_id is not None:
            await self.get_machine(data.machine_id)

        tolerance = ToleranceTable(**data.model_dump())
        self.db.add(tolerance)
        await self.db.flush()
        return tolerance

    async def get_tolerance(self, tolerance_id: uuid.UUID) -> ToleranceTable:
        result = await self.db.execute(
            select(ToleranceTable).where(ToleranceTable.id == tolerance_id)
        )
        tolerance = result.scalar_one_or_none()
        if tolerance is None:
            raise NotFoundError("Tolerance table not found")
        return tolerance

    async def list_tolerances(self, machine_id: uuid.UUID | None = None) -> list[ToleranceTable]:
        query = select(ToleranceTable)
        if machine_id is not None:
            query = query.where(
                (ToleranceTable.machine_id == machine_id) | (ToleranceTable.machine_id.is_(None))
            )
        query = query.order_by(ToleranceTable.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_tolerance(self, tolerance_id: uuid.UUID, data: ToleranceTableUpdate) -> ToleranceTable:
        tolerance = await self.get_tolerance(tolerance_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tolerance, field, value)
        await self.db.flush()
        return tolerance

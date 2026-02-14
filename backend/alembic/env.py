import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings

# Import all models so Alembic can detect them
from app.db.base import Base
from app.domains.auth.models import User, Role, PermissionModel, ElectronicSignature  # noqa: F401
from app.domains.patients.models import Patient, PatientIdentifier, PatientDiagnosis, PatientAllergy  # noqa: F401
from app.domains.audit.models import AuditLog  # noqa: F401
from app.domains.planning.models import (  # noqa: F401
    TreatmentCourse, Prescription, TreatmentPlan, PlanBeam, BeamControlPoint,
)
from app.domains.machines.models import TreatmentMachine, ToleranceTable  # noqa: F401
from app.domains.treatment.models import Fraction, TreatmentSession, BeamDeliveryRecord  # noqa: F401
from app.domains.imaging.models import RTImage, ImageReview  # noqa: F401
from app.domains.scheduling.models import Resource, Appointment, WorkflowTask, Notification  # noqa: F401
from app.domains.qa.models import QAChecklist, QARecord  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

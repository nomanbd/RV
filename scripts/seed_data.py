"""
Seed script for development data.

Creates:
- Default roles and permissions
- Admin user
- Sample patients with diagnoses
- Sample treatment machines with tolerance tables
"""

import asyncio
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.permissions import ROLE_PERMISSIONS, Permission
from app.core.security import get_password_hash
from app.db.base import Base
from app.domains.auth.models import PermissionModel, Role, User, role_permissions
from app.domains.patients.models import Patient, PatientDiagnosis
from app.domains.machines.models import TreatmentMachine, ToleranceTable


async def seed():
    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as db:
        # Check if already seeded
        existing = await db.execute(select(User).where(User.username == "admin"))
        if existing.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return

        print("Seeding database...")

        # --- Create Permissions ---
        permission_models = {}
        for perm in Permission:
            category = perm.value.split(".")[0]
            pm = PermissionModel(
                codename=perm.value,
                description=perm.value.replace(".", " ").replace("_", " ").title(),
                category=category,
            )
            db.add(pm)
            permission_models[perm.value] = pm

        await db.flush()
        print(f"  Created {len(permission_models)} permissions")

        # --- Create Roles ---
        roles = {}
        for role_name, perms in ROLE_PERMISSIONS.items():
            role = Role(
                name=role_name,
                description=f"{role_name.replace('_', ' ').title()} role",
                is_system_role=True,
            )
            db.add(role)
            await db.flush()

            for perm in perms:
                role.permissions.append(permission_models[perm.value])

            roles[role_name] = role

        await db.flush()
        print(f"  Created {len(roles)} roles")

        # --- Create Users ---
        admin = User(
            username="admin",
            email="admin@rv-system.com",
            hashed_password=get_password_hash("admin123"),
            first_name="System",
            last_name="Administrator",
            title=None,
            status="active",
        )
        admin.roles.append(roles["admin"])
        db.add(admin)

        dr_smith = User(
            username="dr.smith",
            email="smith@rv-system.com",
            hashed_password=get_password_hash("password123"),
            first_name="Sarah",
            last_name="Smith",
            title="Dr.",
            professional_id="RO-12345",
            status="active",
        )
        dr_smith.roles.append(roles["radiation_oncologist"])
        db.add(dr_smith)

        physicist = User(
            username="physicist.jones",
            email="jones@rv-system.com",
            hashed_password=get_password_hash("password123"),
            first_name="Michael",
            last_name="Jones",
            title="PhD",
            professional_id="MP-67890",
            status="active",
        )
        physicist.roles.append(roles["physicist"])
        db.add(physicist)

        therapist1 = User(
            username="rtt.williams",
            email="williams@rv-system.com",
            hashed_password=get_password_hash("password123"),
            first_name="Emily",
            last_name="Williams",
            title="RTT",
            professional_id="RT-11111",
            status="active",
        )
        therapist1.roles.append(roles["therapist"])
        db.add(therapist1)

        therapist2 = User(
            username="rtt.brown",
            email="brown@rv-system.com",
            hashed_password=get_password_hash("password123"),
            first_name="James",
            last_name="Brown",
            title="RTT",
            professional_id="RT-22222",
            status="active",
        )
        therapist2.roles.append(roles["therapist"])
        db.add(therapist2)

        dosimetrist = User(
            username="dos.davis",
            email="davis@rv-system.com",
            hashed_password=get_password_hash("password123"),
            first_name="Lisa",
            last_name="Davis",
            title="CMD",
            professional_id="CMD-33333",
            status="active",
        )
        dosimetrist.roles.append(roles["dosimetrist"])
        db.add(dosimetrist)

        await db.flush()
        print("  Created 6 users (admin, oncologist, physicist, 2 therapists, dosimetrist)")

        # --- Create Sample Patients ---
        patients_data = [
            {
                "mrn": "MRN-001",
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": date(1965, 3, 15),
                "sex": "male",
                "phone_primary": "555-0101",
                "email": "john.doe@email.com",
                "address_line1": "123 Main St",
                "city": "Springfield",
                "state": "IL",
                "postal_code": "62701",
                "primary_oncologist_id": dr_smith.id,
                "dicom_patient_id": "PAT001",
            },
            {
                "mrn": "MRN-002",
                "first_name": "Jane",
                "last_name": "Wilson",
                "date_of_birth": date(1978, 8, 22),
                "sex": "female",
                "phone_primary": "555-0102",
                "email": "jane.wilson@email.com",
                "address_line1": "456 Oak Ave",
                "city": "Springfield",
                "state": "IL",
                "postal_code": "62702",
                "primary_oncologist_id": dr_smith.id,
                "dicom_patient_id": "PAT002",
            },
            {
                "mrn": "MRN-003",
                "first_name": "Robert",
                "last_name": "Martinez",
                "date_of_birth": date(1950, 11, 5),
                "sex": "male",
                "phone_primary": "555-0103",
                "address_line1": "789 Elm Blvd",
                "city": "Chicago",
                "state": "IL",
                "postal_code": "60601",
                "primary_oncologist_id": dr_smith.id,
                "dicom_patient_id": "PAT003",
            },
        ]

        patients = []
        for pd in patients_data:
            patient = Patient(**pd)
            db.add(patient)
            patients.append(patient)

        await db.flush()

        # Add diagnoses
        diagnoses = [
            PatientDiagnosis(
                patient_id=patients[0].id,
                icd10_code="C34.1",
                description="Non-small cell lung cancer, right upper lobe",
                site="Right Lung",
                laterality="right",
                is_primary=True,
                diagnosis_date=date(2025, 10, 1),
            ),
            PatientDiagnosis(
                patient_id=patients[1].id,
                icd10_code="C50.9",
                description="Breast cancer, left breast",
                site="Left Breast",
                laterality="left",
                is_primary=True,
                diagnosis_date=date(2025, 9, 15),
            ),
            PatientDiagnosis(
                patient_id=patients[2].id,
                icd10_code="C61",
                description="Prostate cancer",
                site="Prostate",
                is_primary=True,
                diagnosis_date=date(2025, 8, 20),
            ),
        ]
        for dx in diagnoses:
            db.add(dx)

        await db.flush()
        print(f"  Created {len(patients)} patients with diagnoses")

        # --- Create Treatment Machines ---
        machine1 = TreatmentMachine(
            name="TrueBeam-1",
            machine_type="linac",
            manufacturer="Varian",
            model="TrueBeam",
            serial_number="TB-SN-001",
            institution_name="Springfield Cancer Center",
            location="Vault A",
            dicom_ae_title="TRUEBEAM1",
            status="active",
            available_energies=["6MV", "10MV", "6FFF", "10FFF", "6MeV", "9MeV", "12MeV", "15MeV"],
            has_mlc=True,
            mlc_model="Millennium 120",
            mlc_num_leaf_pairs=60,
            has_cbct=True,
            has_epid=True,
            has_kvkv=True,
            max_dose_rate=600,
            commissioning_date=date(2023, 1, 15),
        )
        db.add(machine1)

        machine2 = TreatmentMachine(
            name="VersaHD-1",
            machine_type="linac",
            manufacturer="Elekta",
            model="Versa HD",
            serial_number="VHD-SN-001",
            institution_name="Springfield Cancer Center",
            location="Vault B",
            dicom_ae_title="VERSAHD1",
            status="active",
            available_energies=["6MV", "10MV", "15MV", "6MeV", "9MeV", "12MeV", "15MeV", "18MeV"],
            has_mlc=True,
            mlc_model="Agility",
            mlc_num_leaf_pairs=80,
            has_cbct=True,
            has_epid=True,
            max_dose_rate=600,
            commissioning_date=date(2022, 6, 1),
        )
        db.add(machine2)

        await db.flush()

        # --- Create Tolerance Tables ---
        standard_tol = ToleranceTable(
            name="Standard Photon",
            description="Standard tolerance for conventional photon treatments (3DCRT, IMRT)",
            is_default=True,
            gantry_angle_tol=1.0,
            collimator_angle_tol=1.0,
            couch_angle_tol=1.0,
            couch_vertical_tol=0.5,
            couch_lateral_tol=0.5,
            couch_longitudinal_tol=0.5,
            jaw_x1_tol=0.3,
            jaw_x2_tol=0.3,
            jaw_y1_tol=0.3,
            jaw_y2_tol=0.3,
            mlc_tol=0.3,
            dose_rate_tol=50.0,
            mu_tol=0.5,
            created_by_id=physicist.id,
            approved_by_id=physicist.id,
        )
        db.add(standard_tol)

        srs_tol = ToleranceTable(
            name="SRS/SBRT Tight",
            description="Tight tolerances for stereotactic treatments",
            is_default=False,
            gantry_angle_tol=0.5,
            collimator_angle_tol=0.5,
            couch_angle_tol=0.5,
            couch_vertical_tol=0.2,
            couch_lateral_tol=0.2,
            couch_longitudinal_tol=0.2,
            jaw_x1_tol=0.2,
            jaw_x2_tol=0.2,
            jaw_y1_tol=0.2,
            jaw_y2_tol=0.2,
            mlc_tol=0.2,
            dose_rate_tol=25.0,
            mu_tol=0.2,
            created_by_id=physicist.id,
            approved_by_id=physicist.id,
        )
        db.add(srs_tol)

        electron_tol = ToleranceTable(
            name="Electron",
            description="Standard tolerance for electron beam treatments",
            is_default=False,
            gantry_angle_tol=1.0,
            collimator_angle_tol=1.0,
            couch_angle_tol=1.0,
            couch_vertical_tol=0.5,
            couch_lateral_tol=0.5,
            couch_longitudinal_tol=0.5,
            jaw_x1_tol=0.5,
            jaw_x2_tol=0.5,
            jaw_y1_tol=0.5,
            jaw_y2_tol=0.5,
            dose_rate_tol=50.0,
            mu_tol=1.0,
            created_by_id=physicist.id,
            approved_by_id=physicist.id,
        )
        db.add(electron_tol)

        await db.flush()
        print("  Created 2 treatment machines and 3 tolerance tables")

        await db.commit()
        print("\nSeed data complete!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())

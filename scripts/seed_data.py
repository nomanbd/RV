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

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.permissions import ROLE_PERMISSIONS, Permission
from app.core.security import get_password_hash
from app.db.base import Base
from app.domains.auth.models import PermissionModel, Role, User, role_permissions, user_roles
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
                await db.execute(
                    insert(role_permissions).values(
                        role_id=role.id,
                        permission_id=permission_models[perm.value].id,
                    )
                )

            roles[role_name] = role

        await db.flush()
        print(f"  Created {len(roles)} roles")

        # --- Create Users ---
        users_data = [
            ("admin", "admin@rv-system.com", "admin123", "System", "Administrator", None, None, "admin"),
            ("dr.smith", "smith@rv-system.com", "password123", "Sarah", "Smith", "Dr.", "RO-12345", "radiation_oncologist"),
            ("physicist.jones", "jones@rv-system.com", "password123", "Michael", "Jones", "PhD", "MP-67890", "physicist"),
            ("rtt.williams", "williams@rv-system.com", "password123", "Emily", "Williams", "RTT", "RT-11111", "therapist"),
            ("rtt.brown", "brown@rv-system.com", "password123", "James", "Brown", "RTT", "RT-22222", "therapist"),
            ("dos.davis", "davis@rv-system.com", "password123", "Lisa", "Davis", "CMD", "CMD-33333", "dosimetrist"),
        ]

        user_objects = {}
        for username, email, password, first, last, title, prof_id, role_name in users_data:
            user = User(
                username=username,
                email=email,
                hashed_password=get_password_hash(password),
                first_name=first,
                last_name=last,
                title=title,
                professional_id=prof_id,
                status="active",
            )
            db.add(user)
            await db.flush()
            await db.execute(
                insert(user_roles).values(user_id=user.id, role_id=roles[role_name].id)
            )
            user_objects[username] = user

        admin = user_objects["admin"]
        dr_smith = user_objects["dr.smith"]
        physicist = user_objects["physicist.jones"]

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

from enum import StrEnum
from functools import wraps
from typing import Any, Callable

from fastapi import Depends

from app.core.exceptions import ForbiddenError


class Permission(StrEnum):
    # Patient
    PATIENT_CREATE = "patient.create"
    PATIENT_READ = "patient.read"
    PATIENT_UPDATE = "patient.update"
    PATIENT_DELETE = "patient.delete"

    # Planning
    PLAN_IMPORT = "plan.import"
    PLAN_READ = "plan.read"
    PLAN_REVIEW = "plan.review"
    PLAN_APPROVE = "plan.approve"
    PLAN_PHYSICS_APPROVE = "plan.physics_approve"

    # Prescription
    PRESCRIPTION_CREATE = "prescription.create"
    PRESCRIPTION_APPROVE = "prescription.approve"

    # Treatment
    TREATMENT_CREATE_SESSION = "treatment.create_session"
    TREATMENT_VERIFY_PATIENT = "treatment.verify_patient"
    TREATMENT_VERIFY_BEAM = "treatment.verify_beam"
    TREATMENT_AUTHORIZE_BEAM = "treatment.authorize_beam"
    TREATMENT_RECORD_DELIVERY = "treatment.record_delivery"
    TREATMENT_OVERRIDE_VERIFICATION = "treatment.override_verification"
    TREATMENT_COMPLETE_SESSION = "treatment.complete_session"

    # Machine
    MACHINE_CREATE = "machine.create"
    MACHINE_UPDATE = "machine.update"
    MACHINE_MANAGE_TOLERANCES = "machine.manage_tolerances"

    # Imaging
    IMAGING_IMPORT = "imaging.import"
    IMAGING_REVIEW = "imaging.review"
    IMAGING_APPLY_SHIFTS = "imaging.apply_shifts"

    # Scheduling
    SCHEDULING_CREATE = "scheduling.create"
    SCHEDULING_UPDATE = "scheduling.update"
    SCHEDULING_DELETE = "scheduling.delete"

    # QA
    QA_CREATE_CHECKLIST = "qa.create_checklist"
    QA_SUBMIT_RECORD = "qa.submit_record"
    QA_REVIEW_RECORD = "qa.review_record"

    # Reporting
    REPORT_VIEW = "report.view"
    REPORT_EXPORT = "report.export"

    # Admin
    ADMIN_MANAGE_USERS = "admin.manage_users"
    ADMIN_MANAGE_ROLES = "admin.manage_roles"
    ADMIN_VIEW_AUDIT = "admin.view_audit"
    ADMIN_SYSTEM_CONFIG = "admin.system_config"


# Default role-permission mappings
ROLE_PERMISSIONS: dict[str, list[Permission]] = {
    "admin": list(Permission),
    "radiation_oncologist": [
        Permission.PATIENT_CREATE,
        Permission.PATIENT_READ,
        Permission.PATIENT_UPDATE,
        Permission.PLAN_READ,
        Permission.PLAN_REVIEW,
        Permission.PLAN_APPROVE,
        Permission.PRESCRIPTION_CREATE,
        Permission.PRESCRIPTION_APPROVE,
        Permission.TREATMENT_CREATE_SESSION,
        Permission.TREATMENT_VERIFY_PATIENT,
        Permission.TREATMENT_AUTHORIZE_BEAM,
        Permission.TREATMENT_OVERRIDE_VERIFICATION,
        Permission.IMAGING_REVIEW,
        Permission.IMAGING_APPLY_SHIFTS,
        Permission.SCHEDULING_CREATE,
        Permission.SCHEDULING_UPDATE,
        Permission.QA_REVIEW_RECORD,
        Permission.REPORT_VIEW,
        Permission.REPORT_EXPORT,
    ],
    "physicist": [
        Permission.PATIENT_READ,
        Permission.PLAN_READ,
        Permission.PLAN_REVIEW,
        Permission.PLAN_PHYSICS_APPROVE,
        Permission.TREATMENT_VERIFY_BEAM,
        Permission.TREATMENT_OVERRIDE_VERIFICATION,
        Permission.MACHINE_CREATE,
        Permission.MACHINE_UPDATE,
        Permission.MACHINE_MANAGE_TOLERANCES,
        Permission.IMAGING_REVIEW,
        Permission.QA_CREATE_CHECKLIST,
        Permission.QA_SUBMIT_RECORD,
        Permission.QA_REVIEW_RECORD,
        Permission.REPORT_VIEW,
        Permission.REPORT_EXPORT,
        Permission.ADMIN_VIEW_AUDIT,
    ],
    "therapist": [
        Permission.PATIENT_READ,
        Permission.PATIENT_UPDATE,
        Permission.PLAN_READ,
        Permission.TREATMENT_CREATE_SESSION,
        Permission.TREATMENT_VERIFY_PATIENT,
        Permission.TREATMENT_VERIFY_BEAM,
        Permission.TREATMENT_AUTHORIZE_BEAM,
        Permission.TREATMENT_RECORD_DELIVERY,
        Permission.TREATMENT_COMPLETE_SESSION,
        Permission.IMAGING_IMPORT,
        Permission.IMAGING_REVIEW,
        Permission.IMAGING_APPLY_SHIFTS,
        Permission.SCHEDULING_CREATE,
        Permission.SCHEDULING_UPDATE,
        Permission.QA_SUBMIT_RECORD,
        Permission.REPORT_VIEW,
    ],
    "dosimetrist": [
        Permission.PATIENT_READ,
        Permission.PLAN_IMPORT,
        Permission.PLAN_READ,
        Permission.PLAN_REVIEW,
        Permission.TREATMENT_VERIFY_BEAM,
        Permission.MACHINE_UPDATE,
        Permission.QA_SUBMIT_RECORD,
        Permission.REPORT_VIEW,
    ],
    "nurse": [
        Permission.PATIENT_READ,
        Permission.PATIENT_UPDATE,
        Permission.PLAN_READ,
        Permission.SCHEDULING_CREATE,
        Permission.SCHEDULING_UPDATE,
        Permission.REPORT_VIEW,
    ],
}


def require_permission(permission: Permission) -> Callable:
    """FastAPI dependency factory that checks if the current user has a specific permission."""

    async def _check_permission(current_user: Any = Depends(_get_current_user_for_perms)) -> Any:
        user_permissions = set()
        for role in current_user.roles:
            for perm in role.permissions:
                user_permissions.add(perm.codename)

        if permission.value not in user_permissions:
            raise ForbiddenError(f"Permission '{permission.value}' required")
        return current_user

    return _check_permission


async def _get_current_user_for_perms():
    """Placeholder - replaced by actual dependency in dependencies.py to avoid circular imports."""
    pass

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# --- Auth ---
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


# --- Electronic Signature ---
class ElectronicSignatureRequest(BaseModel):
    username: str
    password: str
    meaning: str = Field(pattern="^(approval|review|verification|authorization|acknowledgment)$")
    reason: str | None = None
    entity_type: str
    entity_id: uuid.UUID


class ElectronicSignatureResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    signer_name: str
    meaning: str
    reason: str | None
    entity_type: str
    entity_id: uuid.UUID
    signed_at: datetime


# --- User ---
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    title: str | None = None
    professional_id: str | None = None
    role_ids: list[uuid.UUID] = []


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    title: str | None = None
    professional_id: str | None = None
    role_ids: list[uuid.UUID] | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    first_name: str
    last_name: str
    title: str | None
    professional_id: str | None
    status: str
    last_login_at: datetime | None
    roles: list["RoleResponse"]
    created_at: datetime

    model_config = {"from_attributes": True}


class UserStatusUpdate(BaseModel):
    status: str = Field(pattern="^(active|inactive|locked)$")


# --- Role ---
class RoleCreate(BaseModel):
    name: str = Field(max_length=100)
    description: str | None = None
    permission_ids: list[uuid.UUID] = []


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    is_system_role: bool
    permissions: list["PermissionResponse"] = []

    model_config = {"from_attributes": True}


# --- Permission ---
class PermissionResponse(BaseModel):
    id: uuid.UUID
    codename: str
    description: str | None
    category: str

    model_config = {"from_attributes": True}

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_signature_hash,
    get_password_hash,
    verify_password,
)
from app.domains.auth.models import ElectronicSignature, PermissionModel, Role, User, user_roles
from app.domains.auth.schemas import (
    ChangePasswordRequest,
    ElectronicSignatureRequest,
    LoginRequest,
    TokenResponse,
    UserCreate,
    UserUpdate,
)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate(self, login: LoginRequest) -> TokenResponse:
        result = await self.db.execute(
            select(User).options(selectinload(User.roles)).where(User.username == login.username)
        )
        user = result.scalar_one_or_none()

        if user is None:
            raise UnauthorizedError("Invalid username or password")

        if user.status == "locked":
            raise UnauthorizedError("Account is locked. Contact administrator.")

        if not verify_password(login.password, user.hashed_password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                user.status = "locked"
            await self.db.flush()
            raise UnauthorizedError("Invalid username or password")

        # Successful login
        user.failed_login_attempts = 0
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.flush()

        access_token = create_access_token({"sub": str(user.id), "username": user.username})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def change_password(self, user_id: uuid.UUID, data: ChangePasswordRequest) -> None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise NotFoundError("User not found")

        if not verify_password(data.current_password, user.hashed_password):
            raise UnauthorizedError("Current password is incorrect")

        user.hashed_password = get_password_hash(data.new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        user.must_change_password = False
        await self.db.flush()

    async def create_electronic_signature(
        self, data: ElectronicSignatureRequest, ip_address: str | None = None, user_agent: str | None = None
    ) -> ElectronicSignature:
        """Create an electronic signature by re-authenticating the user (21 CFR Part 11)."""
        result = await self.db.execute(select(User).where(User.username == data.username))
        user = result.scalar_one_or_none()

        if user is None or not verify_password(data.password, user.hashed_password):
            raise UnauthorizedError("Invalid credentials for electronic signature")

        now = datetime.now(timezone.utc)
        signature = ElectronicSignature(
            user_id=user.id,
            meaning=data.meaning,
            reason=data.reason,
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            signer_name=user.display_name,
            signed_at=now,
            ip_address=ip_address,
            user_agent=user_agent,
            signature_hash=create_signature_hash(
                str(user.id), data.entity_type, str(data.entity_id), now.isoformat()
            ),
        )
        self.db.add(signature)
        await self.db.flush()
        return signature


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, data: UserCreate) -> User:
        # Check uniqueness
        existing = await self.db.execute(
            select(User).where((User.username == data.username) | (User.email == data.email))
        )
        if existing.scalar_one_or_none():
            raise ConflictError("Username or email already exists")

        user = User(
            username=data.username,
            email=data.email,
            hashed_password=get_password_hash(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            title=data.title,
            professional_id=data.professional_id,
        )
        self.db.add(user)
        await self.db.flush()

        # Assign roles
        if data.role_ids:
            roles_result = await self.db.execute(select(Role).where(Role.id.in_(data.role_ids)))
            for role in roles_result.scalars().all():
                user.roles.append(role)
            await self.db.flush()

        return user

    async def get_user(self, user_id: uuid.UUID) -> User:
        result = await self.db.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise NotFoundError("User not found")
        return user

    async def list_users(self, skip: int = 0, limit: int = 50) -> list[User]:
        result = await self.db.execute(
            select(User).options(selectinload(User.roles)).offset(skip).limit(limit).order_by(User.last_name)
        )
        return list(result.scalars().all())

    async def update_user(self, user_id: uuid.UUID, data: UserUpdate) -> User:
        user = await self.get_user(user_id)

        if data.email is not None:
            user.email = data.email
        if data.first_name is not None:
            user.first_name = data.first_name
        if data.last_name is not None:
            user.last_name = data.last_name
        if data.title is not None:
            user.title = data.title
        if data.professional_id is not None:
            user.professional_id = data.professional_id

        if data.role_ids is not None:
            roles_result = await self.db.execute(select(Role).where(Role.id.in_(data.role_ids)))
            user.roles = list(roles_result.scalars().all())

        await self.db.flush()
        return user

    async def update_status(self, user_id: uuid.UUID, status: str) -> User:
        user = await self.get_user(user_id)
        user.status = status
        if status == "active":
            user.failed_login_attempts = 0
        await self.db.flush()
        return user

    async def list_roles(self) -> list[Role]:
        result = await self.db.execute(select(Role).order_by(Role.name))
        return list(result.scalars().all())

    async def list_permissions(self) -> list[PermissionModel]:
        result = await self.db.execute(select(PermissionModel).order_by(PermissionModel.category, PermissionModel.codename))
        return list(result.scalars().all())

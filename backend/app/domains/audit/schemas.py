import uuid
from datetime import datetime

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    username: str | None
    action: str
    entity_type: str
    entity_id: uuid.UUID | None
    entity_description: str | None
    old_values: dict | None
    new_values: dict | None
    changed_fields: list | None
    ip_address: str | None
    recorded_at: datetime

    model_config = {"from_attributes": True}


class AuditLogQuery(BaseModel):
    user_id: uuid.UUID | None = None
    entity_type: str | None = None
    entity_id: uuid.UUID | None = None
    action: str | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None

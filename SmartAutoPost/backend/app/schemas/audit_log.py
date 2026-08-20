from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogCreate(BaseModel):
    user_id: int | None = None
    organization_id: int | None = None

    action: str
    entity_type: str
    entity_id: int | None = None

    ip_address: str | None = None
    user_agent: str | None = None

    details: dict[str, Any] | None = None


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    organization_id: int | None

    action: str
    entity_type: str
    entity_id: int | None

    ip_address: str | None
    user_agent: str | None

    details: dict[str, Any] | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
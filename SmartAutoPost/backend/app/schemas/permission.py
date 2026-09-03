from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None
    module: str


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    module: Optional[str] = None


class PermissionResponse(PermissionBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrganizationMemberRoleBase(BaseModel):
    member_id: int
    role_id: int


class OrganizationMemberRoleCreate(
    OrganizationMemberRoleBase
):
    pass


class OrganizationMemberRoleResponse(
    OrganizationMemberRoleBase
):
    id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
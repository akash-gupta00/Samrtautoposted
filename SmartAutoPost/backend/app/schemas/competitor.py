from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CompetitorBase(BaseModel):
    organization_id: int

    name: str = Field(
        min_length=2,
        max_length=255,
    )

    platform: str = Field(
        min_length=2,
        max_length=50,
    )

    profile_name: str | None = Field(
        default=None,
        max_length=255,
    )

    profile_url: str = Field(
        min_length=5,
    )

    status: str = Field(
        default="active",
        max_length=30,
    )

    notes: str | None = None


class CompetitorCreate(CompetitorBase):
    pass


class CompetitorUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
    )

    platform: str | None = Field(
        default=None,
        min_length=2,
        max_length=50,
    )

    profile_name: str | None = Field(
        default=None,
        max_length=255,
    )

    profile_url: str | None = Field(
        default=None,
        min_length=5,
    )

    status: str | None = Field(
        default=None,
        max_length=30,
    )

    notes: str | None = None


class CompetitorResponse(BaseModel):
    id: int
    organization_id: int
    name: str
    platform: str
    profile_name: str | None
    profile_url: str
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
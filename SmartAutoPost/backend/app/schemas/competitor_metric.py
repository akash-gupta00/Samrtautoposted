from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CompetitorMetricBase(BaseModel):
    competitor_id: int

    followers: int = Field(
        default=0,
        ge=0,
    )

    following: int = Field(
        default=0,
        ge=0,
    )

    total_posts: int = Field(
        default=0,
        ge=0,
    )

    average_likes: float = Field(
        default=0,
        ge=0,
    )

    average_comments: float = Field(
        default=0,
        ge=0,
    )

    average_shares: float = Field(
        default=0,
        ge=0,
    )

    engagement_rate: float = Field(
        default=0,
        ge=0,
    )


class CompetitorMetricCreate(CompetitorMetricBase):
    pass


class CompetitorMetricUpdate(BaseModel):
    followers: int | None = Field(
        default=None,
        ge=0,
    )

    following: int | None = Field(
        default=None,
        ge=0,
    )

    total_posts: int | None = Field(
        default=None,
        ge=0,
    )

    average_likes: float | None = Field(
        default=None,
        ge=0,
    )

    average_comments: float | None = Field(
        default=None,
        ge=0,
    )

    average_shares: float | None = Field(
        default=None,
        ge=0,
    )

    engagement_rate: float | None = Field(
        default=None,
        ge=0,
    )


class CompetitorMetricResponse(BaseModel):
    id: int
    competitor_id: int
    followers: int
    following: int
    total_posts: int
    average_likes: float
    average_comments: float
    average_shares: float
    engagement_rate: float
    recorded_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
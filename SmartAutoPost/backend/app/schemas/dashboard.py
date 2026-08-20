from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    total_posts: int
    scheduled_posts: int
    published_posts: int
    failed_posts: int
    connected_accounts: int
    ai_generations: int


class DashboardRecentPostResponse(BaseModel):
    id: int
    title: str
    caption: str
    status: str
    platform: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    created_at: datetime


class DashboardActivityResponse(BaseModel):
    activity_type: str
    title: str
    description: str
    status: str
    created_at: datetime


class DashboardChartItem(BaseModel):
    label: str
    value: int


class DashboardChartsResponse(BaseModel):
    posts_by_status: list[DashboardChartItem]
    platform_distribution: list[DashboardChartItem]
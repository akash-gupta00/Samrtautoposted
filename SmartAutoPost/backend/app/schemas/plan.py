from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PlanBase(BaseModel):
    name: str
    price: Decimal
    billing_cycle: str = "monthly"
    max_social_accounts: int
    max_posts_per_month: int
    max_ai_generations: int
    max_team_members: int
    max_clients: int
    is_active: bool = True


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[Decimal] = None
    billing_cycle: Optional[str] = None
    max_social_accounts: Optional[int] = None
    max_posts_per_month: Optional[int] = None
    max_ai_generations: Optional[int] = None
    max_team_members: Optional[int] = None
    max_clients: Optional[int] = None
    is_active: Optional[bool] = None


class PlanResponse(PlanBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
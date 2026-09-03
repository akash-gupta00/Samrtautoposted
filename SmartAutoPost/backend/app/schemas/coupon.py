from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CouponCreate(BaseModel):
    organization_id: int
    code: str = Field(min_length=3, max_length=50)
    description: str | None = None

    discount_type: str = Field(
        default="percentage",
        pattern="^(percentage|fixed)$",
    )

    discount_value: Decimal = Field(gt=0)
    minimum_amount: Decimal = Field(default=0, ge=0)
    max_discount: Decimal | None = Field(default=None, gt=0)
    usage_limit: int = Field(default=1, gt=0)
    expires_at: datetime | None = None


class CouponUpdate(BaseModel):
    description: str | None = None

    discount_type: str | None = Field(
        default=None,
        pattern="^(percentage|fixed)$",
    )

    discount_value: Decimal | None = Field(default=None, gt=0)
    minimum_amount: Decimal | None = Field(default=None, ge=0)
    max_discount: Decimal | None = Field(default=None, gt=0)
    usage_limit: int | None = Field(default=None, gt=0)
    is_active: bool | None = None
    expires_at: datetime | None = None


class CouponValidate(BaseModel):
    organization_id: int
    code: str
    amount: Decimal = Field(gt=0)


class CouponValidationResponse(BaseModel):
    valid: bool
    code: str
    discount_amount: Decimal
    final_amount: Decimal
    message: str


class CouponResponse(BaseModel):
    id: int
    organization_id: int
    code: str
    description: str | None
    discount_type: str
    discount_value: Decimal
    minimum_amount: Decimal
    max_discount: Decimal | None
    usage_limit: int
    used_count: int
    is_active: bool
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
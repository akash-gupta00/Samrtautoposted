from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    organization_id: int
    subscription_id: int
    payment_id: int
    plan_name: str
    amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency: str
    status: str
    issued_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
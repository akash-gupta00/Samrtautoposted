from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base_class import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    invoice_number = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    subscription_id = Column(
        Integer,
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    payment_id = Column(
        Integer,
        ForeignKey("payments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    plan_name = Column(
        String(100),
        nullable=False,
    )

    amount = Column(
        Numeric(10, 2),
        nullable=False,
    )

    tax_amount = Column(
        Numeric(10, 2),
        nullable=False,
        default=0,
    )

    total_amount = Column(
        Numeric(10, 2),
        nullable=False,
    )

    currency = Column(
        String(10),
        nullable=False,
        default="INR",
    )

    status = Column(
        String(30),
        nullable=False,
        default="paid",
    )

    issued_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    organization = relationship("Organization")

    subscription = relationship("Subscription")

    payment = relationship("Payment")
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.database.base_class import Base


class Refund(Base):
    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True, index=True)

    payment_id = Column(
        Integer,
        ForeignKey("payments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    amount = Column(
        Numeric(10, 2),
        nullable=False,
    )

    currency = Column(
        String(10),
        nullable=False,
        default="INR",
    )

    reason = Column(
        Text,
        nullable=True,
    )

    status = Column(
        String(30),
        nullable=False,
        default="pending",
    )

    processed_at = Column(
        DateTime,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    payment = relationship("Payment")
    organization = relationship("Organization")
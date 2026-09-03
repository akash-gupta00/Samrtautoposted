from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.base_class import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    subscription_id = Column(
        Integer,
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
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

    payment_gateway = Column(
        String(50),
        nullable=False,
        default="manual",
    )

    transaction_id = Column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )

    status = Column(
        String(30),
        nullable=False,
        default="pending",
    )

    paid_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    subscription = relationship(
        "Subscription",
        back_populates="payments",
    )
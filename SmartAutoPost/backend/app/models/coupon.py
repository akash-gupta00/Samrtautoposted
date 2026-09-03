from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from app.database.base_class import Base


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    code = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    description = Column(
        String(255),
        nullable=True,
    )

    discount_type = Column(
        String(20),
        nullable=False,
        default="percentage",
    )

    discount_value = Column(
        Numeric(10, 2),
        nullable=False,
    )

    minimum_amount = Column(
        Numeric(10, 2),
        nullable=False,
        default=0,
    )

    max_discount = Column(
        Numeric(10, 2),
        nullable=True,
    )

    usage_limit = Column(
        Integer,
        nullable=False,
        default=1,
    )

    used_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    expires_at = Column(
        DateTime,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    organization = relationship(
        "Organization",
    )
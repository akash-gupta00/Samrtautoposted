from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.base_class import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), unique=True, nullable=False)

    price = Column(Numeric(10, 2), nullable=False, default=0)

    billing_cycle = Column(String(20), nullable=False, default="monthly")

    max_social_accounts = Column(Integer, nullable=False, default=1)

    max_posts_per_month = Column(Integer, nullable=False, default=20)

    max_ai_generations = Column(Integer, nullable=False, default=50)

    max_team_members = Column(Integer, nullable=False, default=1)

    max_clients = Column(Integer, nullable=False, default=0)

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    subscriptions = relationship(
        "Subscription",
        back_populates="plan",
    )
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.database.base_class import Base


class CompetitorMetric(Base):
    __tablename__ = "competitor_metrics"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    competitor_id = Column(
        Integer,
        ForeignKey(
            "competitors.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    followers = Column(
        Integer,
        nullable=False,
        default=0,
    )

    following = Column(
        Integer,
        nullable=False,
        default=0,
    )

    total_posts = Column(
        Integer,
        nullable=False,
        default=0,
    )

    average_likes = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    average_comments = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    average_shares = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    engagement_rate = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    recorded_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    competitor = relationship(
        "Competitor",
        back_populates="metrics",
    )
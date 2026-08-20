from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.database.base_class import Base


class PostAnalytic(Base):
    __tablename__ = "post_analytics"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    post_id = Column(
        Integer,
        ForeignKey(
            "posts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    platform = Column(
        String(50),
        nullable=False,
    )

    platform_post_id = Column(
        String(255),
        nullable=True,
    )

    impressions = Column(
        Integer,
        nullable=False,
        default=0,
    )

    reach = Column(
        Integer,
        nullable=False,
        default=0,
    )

    likes = Column(
        Integer,
        nullable=False,
        default=0,
    )

    comments = Column(
        Integer,
        nullable=False,
        default=0,
    )

    shares = Column(
        Integer,
        nullable=False,
        default=0,
    )

    clicks = Column(
        Integer,
        nullable=False,
        default=0,
    )

    saves = Column(
        Integer,
        nullable=False,
        default=0,
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

    post = relationship(
        "Post",
        back_populates="analytics",
    )
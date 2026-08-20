# SQLAlchemy se Column import kar rahe hain.
from sqlalchemy import Column

# Required data types import kar rahe hain.
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text

# Relationship import kar rahe hain.
from sqlalchemy.orm import relationship

# Current date/time ke liye datetime import kar rahe hain.
from datetime import datetime

# Project ka Base import kar rahe hain.
from app.database.base import Base

# Post status enum import kar rahe hain.
from app.core.enums import PostStatus

# Post aur Media association table import kar rahe hain.
from app.models.post_media import post_media


# Post model social media posts ko store karega.
class Post(Base):

    # Database table ka naam posts hoga.
    __tablename__ = "posts"

    # Post ka unique id.
    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # Kis organization ka post hai.
    organization_id = Column(
        Integer,
        ForeignKey(
            "organizations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # Kis social account par publish hoga.
    social_account_id = Column(
        Integer,
        ForeignKey(
            "social_accounts.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # Post ka title.
    title = Column(
        String(255),
        nullable=False,
    )

    # Post ka caption/content.
    caption = Column(
        Text,
        nullable=False,
    )

    # Post ka status.
    status = Column(
        String(50),
        default=PostStatus.DRAFT.value,
        nullable=False,
        index=True,
    )

    # Post kab schedule hai.
    scheduled_at = Column(
        DateTime,
        nullable=True,
    )

    # Post kab publish hua.
    published_at = Column(
        DateTime,
        nullable=True,
    )

    # Post kab create hua.
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Post aur Media ke beech many-to-many relationship.
    media = relationship(
        "Media",
        secondary=post_media,
        back_populates="posts",
    )

    # Post aur PostAnalytic ke beech one-to-many relationship.
    analytics = relationship(
        "PostAnalytic",
        back_populates="post",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
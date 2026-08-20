from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database.base_class import Base


class Competitor(Base):
    __tablename__ = "competitors"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    organization_id = Column(
        Integer,
        ForeignKey(
            "organizations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    name = Column(
        String(255),
        nullable=False,
    )

    platform = Column(
        String(50),
        nullable=False,
        index=True,
    )

    profile_name = Column(
        String(255),
        nullable=True,
    )

    profile_url = Column(
        Text,
        nullable=False,
    )

    status = Column(
        String(30),
        nullable=False,
        default="active",
    )

    notes = Column(
        Text,
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

    # Relationship with Organization
    organization = relationship(
        "Organization",
    )

    # Relationship with CompetitorMetric
    metrics = relationship(
        "CompetitorMetric",
        back_populates="competitor",
        cascade="all, delete-orphan",
    )
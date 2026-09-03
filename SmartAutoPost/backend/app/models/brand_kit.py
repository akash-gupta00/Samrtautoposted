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


class BrandKit(Base):
    __tablename__ = "brand_kits"

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

    brand_name = Column(
        String(255),
        nullable=False,
    )

    logo_url = Column(
        Text,
        nullable=True,
    )

    primary_color = Column(
        String(20),
        nullable=True,
    )

    secondary_color = Column(
        String(20),
        nullable=True,
    )

    font_family = Column(
        String(100),
        nullable=True,
    )

    tone_of_voice = Column(
        String(100),
        nullable=True,
    )

    default_hashtags = Column(
        Text,
        nullable=True,
    )

    website_url = Column(
        String(255),
        nullable=True,
    )

    contact_email = Column(
        String(255),
        nullable=True,
    )

    contact_phone = Column(
        String(30),
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

    organization = relationship(
        "Organization",
        back_populates="brand_kits",
    )
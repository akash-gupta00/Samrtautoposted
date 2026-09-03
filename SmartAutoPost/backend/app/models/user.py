from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
)

from sqlalchemy.orm import relationship

from app.database.base_class import Base


class User(Base):

    __tablename__ = "users"


    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )


    name = Column(
        String(255),
        nullable=False,
    )


    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )


    password_hash = Column(
        String(255),
        nullable=True,
    )


    role = Column(
        String(50),
        default="user",
        nullable=False,
    )


    status = Column(
        String(20),
        default="pending",
        nullable=False,
    )


    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )


    is_verified = Column(
        Boolean,
        default=False,
        nullable=False,
    )


    # ==========================
    # EMAIL VERIFICATION
    # ==========================

    email_verification_token = Column(
        String(255),
        nullable=True,
    )


    # ==========================
    # PASSWORD RESET
    # ==========================

    password_reset_token = Column(
        String(255),
        nullable=True,
    )


    password_reset_expires = Column(
        DateTime,
        nullable=True,
    )


    # ==========================
    # TWO FACTOR AUTH
    # ==========================

    two_factor_secret = Column(
        String(100),
        nullable=True,
    )


    two_factor_enabled = Column(
        Boolean,
        default=False,
        nullable=False,
    )


    # ==========================
    # SOCIAL LOGIN IDS
    # ==========================


    facebook_id = Column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )


    google_id = Column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )


    linkedin_id = Column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )


    instagram_id = Column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )


    twitter_id = Column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )


    # ==========================
    # SOCIAL PROFILE DATA
    # ==========================


    profile_image = Column(
        String(500),
        nullable=True,
    )


    phone = Column(
        String(50),
        nullable=True,
    )


    auth_provider = Column(
        String(50),
        default="email",
        nullable=False,
    )


    # ==========================
    # ACCOUNT DATES
    # ==========================


    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


    # ==========================
    # RELATIONS
    # ==========================

    audit_logs = relationship(
        "AuditLog",
        back_populates="user",
        passive_deletes=True,
    )
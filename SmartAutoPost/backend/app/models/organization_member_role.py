from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
)

from sqlalchemy.orm import relationship

from app.database.base_class import Base


class OrganizationMemberRole(Base):
    __tablename__ = "organization_member_roles"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    member_id = Column(
        Integer,
        ForeignKey(
            "organization_members.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    role_id = Column(
        Integer,
        ForeignKey(
            "roles.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    member = relationship(
        "OrganizationMember",
        back_populates="member_roles",
    )

    role = relationship(
        "Role",
        back_populates="member_roles",
    )

    __table_args__ = (
        UniqueConstraint(
            "member_id",
            "role_id",
            name="uq_organization_member_role",
        ),
    )
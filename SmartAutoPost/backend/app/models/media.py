from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.models.post_media import post_media


class Media(Base):

    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)

    filename = Column(String(255), nullable=False)

    file_url = Column(String(500), nullable=False)

    file_type = Column(String(255), nullable=False)

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    organization = relationship(
        "Organization",
        back_populates="media",
    )

    posts = relationship(
        "Post",
        secondary=post_media,
        back_populates="media",
    )
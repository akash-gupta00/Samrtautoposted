from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime

from app.database.base import Base


class AIGeneration(Base):

    __tablename__ = "ai_generations"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False
    )

    # caption, hashtags, seo, image_prompt, gemini
    generation_type = Column(String(50), nullable=False)

    # facebook, instagram, linkedin, threads
    platform = Column(String(50), nullable=True)

    prompt = Column(Text, nullable=False)

    generated_content = Column(Text, nullable=True)

    # success / failed
    status = Column(String(30), nullable=False, default="success")

    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
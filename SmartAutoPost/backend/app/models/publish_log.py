# SQLAlchemy columns import kar rahe hain.
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey

# Current time ke liye datetime import kar rahe hain.
from datetime import datetime

# Base import kar rahe hain.
from app.database.base import Base


# Publish logs table ka model.
class PublishLog(Base):

    # Database table name.
    __tablename__ = "publish_logs"

    # Unique id.
    id = Column(Integer, primary_key=True, index=True)

    # Kis post ka publish log hai.
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)

    # Platform name jaise facebook/linkedin.
    platform = Column(String(100), nullable=False)

    # Platform se mila post id.
    platform_post_id = Column(String(255), nullable=True)

    # Publish status.
    status = Column(String(50), nullable=False)

    # Full response store karne ke liye.
    response = Column(Text, nullable=True)

    # Log create time.
    created_at = Column(DateTime, default=datetime.utcnow)
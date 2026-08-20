# SQLAlchemy se Column import kar rahe hain.
# Column database table ke fields banane ke liye use hota hai.
from sqlalchemy import Column

# Integer, DateTime aur String datatype import kar rahe hain.
from sqlalchemy import Integer, DateTime, String

# ForeignKey import kar rahe hain.
# Isse schedule ko post table se connect karenge.
from sqlalchemy import ForeignKey

# Relationship import kar rahe hain.
# Post aur Schedule ke beech relation banane ke liye.
from sqlalchemy.orm import relationship

# Current time ke liye datetime import kar rahe hain.
from datetime import datetime

# Base import kar rahe hain.
# Har model Base ko inherit karta hai.
from app.database.base import Base


# PostSchedule model schedule table ko represent karega.
class PostSchedule(Base):

    # Database table ka naam.
    __tablename__ = "post_schedules"

    # Schedule ka unique id.
    id = Column(Integer, primary_key=True, index=True)

    # Kis post ko schedule kiya gaya hai.
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)

    # Post kab publish hoga.
    schedule_time = Column(DateTime, nullable=False)

    # Timezone store kar rahe hain.
    timezone = Column(String(100), default="Asia/Kolkata", nullable=False)

    # Schedule ka status.
    # pending, processing, published, failed
    status = Column(String(50), default="pending", nullable=False)

    # Retry count agar publish fail ho jaye.
    retry_count = Column(Integer, default=0, nullable=False)

    # Schedule kab create hua.
    created_at = Column(DateTime, default=datetime.utcnow)

    # Post ke saath relationship.
    post = relationship("Post")
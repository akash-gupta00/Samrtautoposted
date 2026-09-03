# SQLAlchemy se Column import kar rahe hain.
# Column database table ke fields banane ke liye use hota hai.
from sqlalchemy import Column

# SQLAlchemy datatypes import kar rahe hain.
# Integer id ke liye, String text values ke liye, DateTime time ke liye.
from sqlalchemy import Integer, String, DateTime

# ForeignKey import kar rahe hain.
# Isse organization ko user se connect karenge.
from sqlalchemy import ForeignKey

# Python datetime import kar rahe hain.
# created_at aur updated_at me current time save karne ke liye.
from datetime import datetime

# Project ka Base import kar rahe hain.
# Har model Base ko inherit karega.
from app.database.base_class import Base

# Relationship banane ke liye import.
from sqlalchemy.orm import relationship

# Organization model class bana rahe hain.
# Ye database me organizations table represent karegi.
class Organization(Base):

    # Database table ka naam organizations hoga.
    __tablename__ = "organizations"

    # Organization ka unique id.
    id = Column(Integer, primary_key=True, index=True)

    # Organization ka naam.
    # Example: Teknowxa, ABC Digital, Personal Brand
    name = Column(String(255), nullable=False)

    # Organization ka unique slug.
    # Example: teknowxa, abc-digital
    slug = Column(String(255), unique=True, index=True, nullable=False)

    # Organization ka industry.
    # Example: IT Services, Hospital, School, Restaurant
    industry = Column(String(255), nullable=True)

    # Organization ka timezone.
    # Default India timezone rakha hai.
    timezone = Column(String(100), default="Asia/Kolkata", nullable=False)

    # Organization ka language.
    # Default English rakha hai.
    language = Column(String(50), default="en", nullable=False)

    # Organization owner ka user id.
    # Ye users table ke id column se linked hai.
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Organization kab create hui.
    created_at = Column(DateTime, default=datetime.utcnow)

    # Organization last update kab hui.
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    
        # Organization ke saare media ko access karne ke liye relationship.
    media = relationship(
        "Media",
        back_populates="organization",
    )
    subscriptions = relationship(
    "Subscription",
    back_populates="organization",
    cascade="all, delete-orphan",
   )
    
    brand_kits = relationship(
        "BrandKit",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    roles = relationship(
    "Role",
    back_populates="organization",
    cascade="all, delete-orphan",
    )
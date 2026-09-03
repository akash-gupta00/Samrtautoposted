# SQLAlchemy Column import
from sqlalchemy import Column

# SQLAlchemy datatypes
from sqlalchemy import (
    Integer,
    String,
    Boolean,
    DateTime,
)

# Foreign key
from sqlalchemy import ForeignKey

# datetime
from datetime import datetime

# Base model
from app.database.base_class import Base



# =========================================================
# Social Account Model
# =========================================================

class SocialAccount(Base):

    __tablename__ = "social_accounts"



    # Primary ID
    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )



    # Organization relation
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
    )



    # Platform name
    # facebook
    # instagram
    # linkedin
    # threads
    provider = Column(
        String(50),
        nullable=False,
    )



    # Account display name
    # Example:
    # My Facebook Page
    # My Instagram Account
    account_name = Column(
        String(255),
        nullable=False,
    )



    # =====================================================
    # SOCIAL PLATFORM IDS
    # =====================================================


    # Facebook Page ID
    # Instagram Business Account ID
    page_id = Column(
        String(255),
        nullable=True,
    )



    # Instagram User ID (optional)
    instagram_id = Column(
        String(255),
        nullable=True,
    )



    # =====================================================
    # OAUTH TOKENS
    # =====================================================


    # Access Token
    access_token = Column(
        String,
        nullable=False,
    )



    # Refresh Token
    refresh_token = Column(
        String,
        nullable=True,
    )



    # Token expiry
    expires_at = Column(
        DateTime,
        nullable=True,
    )



    # Account active status
    is_active = Column(
        Boolean,
        default=True,
    )



    # Created date
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )
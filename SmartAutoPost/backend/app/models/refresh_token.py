from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app.database.base import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # ✅ FIX: Integer (kyunki users.id Integer hai)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    token = Column(String(500), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
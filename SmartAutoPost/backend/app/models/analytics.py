from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

# Base import fix: pehle models/base check karega, fir database/base
try:
    from app.database.base import Base
except ImportError:
    try:
        from app.database.base_class import Base
    except ImportError:
        try:
            from app.models.user import Base
        except ImportError:
            try:
                from app.models.post import Base
            except ImportError:
                from sqlalchemy.ext.declarative import declarative_base
                Base = declarative_base()


class AnalyticsRecord(Base):
    __tablename__ = "analytics_records"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    reach = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
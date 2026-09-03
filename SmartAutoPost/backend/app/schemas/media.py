# Pydantic ka BaseModel import kar rahe hain.
# Isse API response schema banate hain.
from pydantic import BaseModel


# datetime import kar rahe hain.
# created_at field ke liye use hoga.
from datetime import datetime


# Media response schema bana rahe hain.
# Ye API response ka format define karega.
class MediaResponse(BaseModel):

    # Media ka unique id.
    id: int

    # File ka original naam.
    filename: str

    # File ka saved path ya URL.
    file_url: str

    # File ka type.
    file_type: str

    # Organization id.
    organization_id: int

    # File kab upload hui.
    created_at: datetime

    # SQLAlchemy model ko Pydantic response me convert karne ke liye.
    class Config:

        # ORM object support enable kar rahe hain.
        from_attributes = True
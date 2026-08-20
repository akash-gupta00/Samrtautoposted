from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AIGenerationResponse(BaseModel):

    id: int
    user_id: int
    organization_id: int
    generation_type: str
    platform: Optional[str] = None
    prompt: str
    generated_content: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
from pydantic import BaseModel
from typing import List


class GeminiRequest(BaseModel):
    keyword: str
    platform: str
    task_type: str
    tone: str = "professional"
    language: str = "Hinglish"


class GeminiResponse(BaseModel):
    result: str
    task_type: str
    platform: str
    language: str
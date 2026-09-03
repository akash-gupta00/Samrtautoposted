from pydantic import BaseModel
from typing import List


class HashtagRequest(BaseModel):
    keyword: str
    platform: str
    language: str = "Hinglish"


class HashtagResponse(BaseModel):
    hashtags: List[str]
    platform: str
    language: str
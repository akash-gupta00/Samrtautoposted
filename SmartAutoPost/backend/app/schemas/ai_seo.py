from pydantic import BaseModel
from typing import List


class SEORequest(BaseModel):
    keyword: str
    platform: str
    language: str = "English"


class SEOResponse(BaseModel):
    title: str
    meta_description: str
    keywords: List[str]
    platform: str
    language: str
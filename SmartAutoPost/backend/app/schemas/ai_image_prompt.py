from pydantic import BaseModel


class ImagePromptRequest(BaseModel):
    keyword: str
    platform: str
    style: str = "modern"
    language: str = "English"


class ImagePromptResponse(BaseModel):
    image_prompt: str
    platform: str
    style: str
    language: str
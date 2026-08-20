# Pydantic ka BaseModel import kar rahe hain.
# Isse request aur response schema banate hain.
from pydantic import BaseModel


# Caption generate karne ke liye request schema.
class CaptionRequest(BaseModel):

    # Kis topic/keyword par caption chahiye.
    keyword: str

    # Kis platform ke liye caption chahiye.
    platform: str

    # Caption ka tone kaisa hoga.
    tone: str = "professional"

    # Caption kis language me chahiye.
    language: str = "Hinglish"


# Caption response schema.
class CaptionResponse(BaseModel):

    # Generated caption.
    caption: str

    # Platform name.
    platform: str

    # Tone.
    tone: str

    # Language.
    language: str
# Pydantic se BaseModel import kar rahe hain.
from pydantic import BaseModel


# Social account connect karne ke liye request schema.
class SocialAccountCreate(BaseModel):

    # Organization id jisme social account connect hoga.
    organization_id: int

    # Platform/provider ka naam.
    # Example: facebook, instagram, linkedin
    provider: str

    # Social account ka display name.
    account_name: str

    # Access token.
    access_token: str

    # Refresh token optional hai.
    refresh_token: str | None = None


# Social account response schema.
class SocialAccountResponse(BaseModel):

    id: int
    organization_id: int
    provider: str
    account_name: str
    is_active: bool

    class Config:
        from_attributes = True
# Pydantic se BaseModel aur Field import kar rahe hain.
# BaseModel request/response validation ke liye hota hai.
# Field validation rules set karne ke liye hota hai.
from pydantic import BaseModel, Field


# Organization create karne ke liye request schema.
class OrganizationCreate(BaseModel):

    # Organization ka naam.
    # Minimum 2 aur maximum 255 characters allowed.
    name: str = Field(min_length=2, max_length=255)

    # Business industry optional hai.
    # Example: IT Services, Hospital, School
    industry: str | None = None

    # Timezone default Asia/Kolkata.
    timezone: str = "Asia/Kolkata"

    # Language default English.
    language: str = "en"


# Organization response schema.
class OrganizationResponse(BaseModel):

    # Organization id.
    id: int

    # Organization name.
    name: str

    # Organization slug.
    slug: str

    # Industry.
    industry: str | None

    # Timezone.
    timezone: str

    # Language.
    language: str

    # Owner user id.
    owner_id: int

    # SQLAlchemy object ko response me convert karne ke liye.
    class Config:
        from_attributes = True
        
# Organization update karne ke liye request schema.
# Sab fields optional hain kyunki user name ya industry me se kuch bhi update kar sakta hai.
class OrganizationUpdate(BaseModel):

    # Organization ka new name optional hai.
    name: str | None = Field(default=None, min_length=2, max_length=255)

    # Industry optional hai.
    industry: str | None = None

    # Timezone optional hai.
    timezone: str | None = None

    # Language optional hai.
    language: str | None = None
# Pydantic se BaseModel aur Field import kar rahe hain.
from pydantic import BaseModel, Field


# Member invite request schema.
class MemberInvite(BaseModel):

    # Jis user ko add karna hai uska email.
    email: str

    # Us user ka role.
    # Example: admin, editor, viewer
    role: str = Field(default="viewer")
    
    

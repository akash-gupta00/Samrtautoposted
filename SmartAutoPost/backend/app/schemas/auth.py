from pydantic import BaseModel, EmailStr
from typing import Optional

# ============================================================
# ✅ EXISTING SCHEMAS (user.py me already hain)
# ============================================================

# ============================================================
# ✅ NAYE SCHEMAS — AUTH KE LIYE
# ============================================================

class RefreshTokenRequest(BaseModel):
    refresh_token: str


class VerifyEmailRequest(BaseModel):
    token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class TwoFactorRequest(BaseModel):
    otp: str
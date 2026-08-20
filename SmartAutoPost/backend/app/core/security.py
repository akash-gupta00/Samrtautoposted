# ============================================================
# ✅ EXISTING CODE — BILKUL WAISA HI (KOI CHANGE NAHI)
# ============================================================

# datetime se datetime aur timedelta import kar rahe hain.
# datetime current time ke liye aur timedelta expiry time calculate karne ke liye use hota hai.
from datetime import datetime, timedelta

# jose library se jwt aur JWTError import kar rahe hain.
# jwt token create aur decode karega.
# JWTError invalid ya expired token ko handle karega.
from jose import jwt, JWTError

# passlib se CryptContext import kar rahe hain.
# Password ko hash aur verify karne ke liye.
from passlib.context import CryptContext

# Project settings import kar rahe hain.
# SECRET_KEY, ALGORITHM aur expiry time config.py se aayega.
from app.core.config import settings


# Password hashing context bana rahe hain.
# bcrypt algorithm password ko secure hash me convert karega.
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# Plain password ko hash password me convert karne wala function.
def hash_password(password: str):

    # Original password ko hash karke return kar rahe hain.
    return pwd_context.hash(password)


# Plain password aur database ke hashed password ko compare karega.
def verify_password(plain_password: str, hashed_password: str):

    # Password sahi hua to True return karega.
    return pwd_context.verify(
        plain_password,
        hashed_password
    )


# JWT Access Token create karne wala function.
def create_access_token(data: dict):

    # Original dictionary ki copy bana rahe hain.
    to_encode = data.copy()

    # Token kitni der valid rahega uska time calculate kar rahe hain.
    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    # Token ke andar expiry time add kar rahe hain.
    to_encode.update(
        {
            "exp": expire
        }
    )

    # JWT Token create kar rahe hain.
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    # Final JWT Token return kar rahe hain.
    return encoded_jwt


# JWT Token decode karne wala function.
# Decode ka matlab token ke andar ka data padhna.
def decode_access_token(token: str):

    try:

        # Token ko decode kar rahe hain.
        # Agar token valid hai to payload return hoga.
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # Token ka data return kar rahe hain.
        return payload

    except JWTError:

        # Agar token invalid ya expired hua to None return karenge.
        return None


# ============================================================
# ✅ NAYA FUNCTION 1: CREATE REFRESH TOKEN
# ============================================================

def create_refresh_token(data: dict):
    """
    Refresh Token create karega.
    Refresh token access token se zyada der tak valid rehta hai (7 days).
    Iska use naya access token generate karne ke liye hota hai.
    """

    # Original dictionary ki copy bana rahe hain.
    to_encode = data.copy()

    # Refresh token kitni der valid rahega (7 days).
    expire = datetime.utcnow() + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    # Token ke andar expiry time add kar rahe hain.
    to_encode.update(
        {
            "exp": expire
        }
    )

    # Refresh Token create kar rahe hain.
    # NOTE: Different secret key use kar rahe hain security ke liye.
    encoded_jwt = jwt.encode(
        to_encode,
        settings.REFRESH_SECRET_KEY,  # Different secret key
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


# ============================================================
# ✅ NAYA FUNCTION 2: DECODE REFRESH TOKEN
# ============================================================

def decode_refresh_token(token: str):
    """
    Refresh token decode karega.
    Agar token valid hai to payload return karega, warna None.
    """

    try:

        payload = jwt.decode(
            token,
            settings.REFRESH_SECRET_KEY,  # Different secret key
            algorithms=[settings.ALGORITHM]
        )

        return payload

    except JWTError:

        return None


# ============================================================
# ❌ HATA DIYA: get_current_user, get_current_active_user,
# get_current_admin_user, aur OAuth2PasswordBearer scheme
# ============================================================
# Ye sab pehle yahan duplicate define the (OAuth2PasswordBearer wale).
# Isi wajah se Swagger "Available authorizations" popup me
# do schemes (HTTPBearer + OAuth2PasswordBearer) dikh rahe the.
#
# Actual user-fetching logic ab sirf ek jagah hai:
#     app/dependencies/auth.py   (HTTPBearer wala, jo already sahi hai)
#
# Jis bhi file ko current user chahiye, wahan se import karo:
#     from app.dependencies.auth import get_current_user
#
# Agar "active user" ya "admin user" check bhi chahiye, to wo
# helper functions bhi app/dependencies/auth.py me hi add karo,
# security.py me nahi — taaki sirf ek hi auth scheme rahe
# aur Swagger me sirf ek hi "Authorize" option aaye.
# ============================================================
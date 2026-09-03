# FastAPI se Depends aur HTTPException import kar rahe hain.
# Depends dependency injection ke liye hota hai.
# HTTPException error response dene ke liye hota hai.
from fastapi import Depends, HTTPException

# HTTPBearer Authorization header se Bearer token read karta hai.
# Isse Swagger me token paste karne ka option milega.
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# SQLAlchemy Session import kar rahe hain.
# Database query chalane ke liye.
from sqlalchemy.orm import Session

# Database session dependency import kar rahe hain.
from app.database.session import get_db

# JWT token decode function import kar rahe hain.
from app.core.security import decode_access_token

# User model import kar rahe hain.
from app.models.user import User


# HTTP Bearer security scheme bana rahe hain.
# auto_error=True ka matlab token missing hua to automatically error milega.
bearer_scheme = HTTPBearer(auto_error=True)


# Current logged-in user return karne wala function.
def get_current_user(

    # Authorization header se Bearer token read hoga.
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),

    # Database session milega.
    db: Session = Depends(get_db)

):

    # credentials.credentials ke andar actual token hota hai.
    token = credentials.credentials

    # JWT token decode kar rahe hain.
    payload = decode_access_token(token)

    # Agar token invalid ya expired hai to error denge.
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    # Token ke andar se email nikal rahe hain.
    email = payload.get("sub")

    # Agar token me email nahi mila to error denge.
    if email is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload"
        )

    # Email ke basis par database me user search kar rahe hain.
    user = db.query(User).filter(User.email == email).first()

    # Agar user database me nahi mila to error denge.
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    # Current logged-in user return kar rahe hain.
    return user
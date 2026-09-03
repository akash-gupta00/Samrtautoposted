# Pydantic se BaseModel, EmailStr aur Field import kar rahe hain.
# BaseModel request/response validation ke liye hota hai.
# EmailStr valid email format check karta hai.
# Field se hum min/max length validation laga sakte hain.
from pydantic import BaseModel, EmailStr, Field


# Register request ke liye schema.
class UserCreate(BaseModel):

    # User ka naam.
    # Minimum 2 aur maximum 100 characters allowed.
    name: str = Field(min_length=2, max_length=100)

    # User ka email.
    # EmailStr invalid email ko reject karega.
    email: EmailStr

    # User ka password.
    # bcrypt maximum 72 bytes password accept karta hai,
    # isliye max_length=72 rakha hai.
    password: str = Field(min_length=6, max_length=72)


# Register response ke liye schema.
class UserResponse(BaseModel):

    # User id.
    id: int

    # User name.
    name: str

    # User email.
    email: EmailStr

    # User active status.
    is_active: bool

    # User ka role (admin / user).
    role: str = "user"

    # User kis tarike se login/register hua (email / facebook / instagram / linkedin).
    auth_provider: str = "email"

    # SQLAlchemy model object ko JSON response me convert karne ke liye.
    class Config:
        from_attributes = True
        
# Login request ke liye schema.
# Isme user sirf email aur password bhejega.
class UserLogin(BaseModel):

    # User ka email.
    # EmailStr check karega email valid format me hai ya nahi.
    email: EmailStr

    # User ka password.
    # Minimum 6 aur maximum 72 characters allowed.
    password: str = Field(min_length=6, max_length=72)
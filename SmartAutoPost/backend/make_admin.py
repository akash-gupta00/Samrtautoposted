"""
Ye script kisi bhi existing user ka role "admin" set kar deta hai,
taaki wo sidebar me sab Management + Finance & System sections
(Organizations, Billing, Roles, Invoices, etc.) dekh sake.

USAGE (backend folder ke andar, venv activate karke):
    python make_admin.py aapka_email@example.com
"""

import sys

from app.database.session import SessionLocal
from app.models.user import User


def make_admin(email: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ Koi user is email se nahi mila: {email}")
            return
        user.role = "admin"
        db.commit()
        print(f"✅ '{user.name}' ({user.email}) ab ADMIN ban gaya hai.")
        print("   Browser me logout karke dobara login karein taaki naya role load ho.")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python make_admin.py aapka_email@example.com")
        sys.exit(1)
    make_admin(sys.argv[1])

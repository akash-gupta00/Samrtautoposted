"""
Ye script aapka FIXED ADMIN account seedha database me bana deta hai
(ya agar already hai to password/role update kar deta hai).

Email:    akashkr915520@gmail.com
Password: akashkr098

USAGE (backend folder ke andar, venv activate karke):
    python create_admin.py
"""

from app.database.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password
from app.api.auth import get_or_create_personal_organization


ADMIN_EMAIL = "akashkr915520@gmail.com"
ADMIN_PASSWORD = "akashkr098"
ADMIN_NAME = "Akash Kumar"


def create_or_update_admin():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == ADMIN_EMAIL).first()

        if user:
            user.password_hash = hash_password(ADMIN_PASSWORD)
            user.role = "admin"
            user.is_active = True
            user.is_verified = True
            db.commit()
            db.refresh(user)
            print(f"✅ Existing account update ho gaya: {user.email}")
        else:
            user = User(
                name=ADMIN_NAME,
                email=ADMIN_EMAIL,
                password_hash=hash_password(ADMIN_PASSWORD),
                role="admin",
                status="active",
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✅ Naya ADMIN account ban gaya: {user.email}")

        org = get_or_create_personal_organization(db=db, user=user)

        print(f"   Role        : {user.role}")
        print(f"   Password    : {ADMIN_PASSWORD}")
        print(f"   Organization: {org.name}")
        print("")
        print("Ab is email/password se login karein.")
    finally:
        db.close()


if __name__ == "__main__":
    create_or_update_admin()

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Request,
)

from fastapi.responses import HTMLResponse

from sqlalchemy.orm import Session

from datetime import datetime, timedelta
from fastapi.responses import RedirectResponse

import secrets
import httpx
import requests

from urllib.parse import urlencode


from app.database.session import get_db

from app.models.social_account import SocialAccount

from app.models.user import User

from app.models.refresh_token import RefreshToken

from app.models.organization import Organization

from app.models.organization_member import OrganizationMember


from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserLogin,
)


from app.schemas.auth import (
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    TwoFactorRequest,
)


from app.schemas.audit_log import AuditLogCreate


from app.services.audit_log_service import (
    AuditLogService,
)


from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)


from app.dependencies.auth import (
    get_current_user,
)


from app.core.config import settings
from datetime import datetime, timedelta



# ============================================================
# EMAIL SERVICE
# ============================================================


try:

    from app.services.email import (
        send_verification_email,
        send_password_reset_email,
    )


except ImportError:


    def send_verification_email(
        to_email,
        token
    ):
        print(
            f"Verification email: {to_email} {token}"
        )



    def send_password_reset_email(
        to_email,
        token
    ):
        print(
            f"Reset email: {to_email} {token}"
        )





# ============================================================
# ROUTER
# ============================================================


router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


def get_or_create_personal_organization(db: Session, user: User) -> Organization:
    existing_org = (
        db.query(Organization)
        .filter(Organization.owner_id == user.id)
        .first()
    )
    if existing_org:
        return existing_org

    base_slug = (
        (user.name or user.email or f"user-{user.id}")
        .lower().strip().replace(" ", "-")
    )
    slug = f"{base_slug}-{user.id}"

    new_org = Organization(
        name=f"{user.name or 'My'} Workspace",
        slug=slug,
        industry=None,
        timezone="Asia/Kolkata",
        language="en",
        owner_id=user.id,
    )
    db.add(new_org)
    db.flush()

    owner_member = OrganizationMember(
        organization_id=new_org.id,
        user_id=user.id,
        role="owner",
    )
    db.add(owner_member)
    db.commit()
    db.refresh(new_org)
    return new_org





# ============================================================
# AUDIT LOG HELPER
# ============================================================


def create_auth_audit_log(
    db: Session,
    request: Request,
    action: str,
    user_id: int | None = None,
    entity_id: int | None = None,
    details: dict | None = None,
):

    try:

        AuditLogService.create_log(

            db=db,

            audit_data=AuditLogCreate(

                user_id=user_id,

                organization_id=None,

                action=action,

                entity_type="user",

                entity_id=entity_id,

                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),

                user_agent=request.headers.get(
                    "user-agent"
                ),

                details=details,
            )
        )


    except Exception as error:

        db.rollback()

        print(
            f"Audit log error: {error}"
        )





# ============================================================
# REGISTER API
# ============================================================


@router.post(
    "/register",
    response_model=UserResponse
)
def register_user(

    user_data: UserCreate,

    request: Request,

    db: Session = Depends(get_db),

):


    existing_user = (

        db.query(User)

        .filter(
            User.email == user_data.email
        )

        .first()

    )



    if existing_user:

        raise HTTPException(

            status_code=400,

            detail="Email already registered"

        )



    hashed_password = hash_password(

        user_data.password

    )



    new_user = User(

        name=user_data.name,

        email=user_data.email,

        password_hash=hashed_password,

        # Har naya register hua user by default "user" (limited)
        # role ke saath banta hai. Sirf ek founder/admin account
        # hai jise "create_admin.py" se manually admin banaya
        # gaya hai.
        role="user",

    )



    db.add(new_user)

    db.commit()

    db.refresh(new_user)

    # Naye user ke liye khud-ba-khud personal organization.
    get_or_create_personal_organization(db=db, user=new_user)





    create_auth_audit_log(

        db=db,

        request=request,

        user_id=new_user.id,

        entity_id=new_user.id,

        action="user_registered",

        details={

            "email": new_user.email,

            "name": new_user.name,

        }

    )



    return new_user






# ============================================================
# LOGIN API
# ============================================================



@router.post("/login")
def login_user(

    user_data: UserLogin,

    request: Request,

    db: Session = Depends(get_db),

):


    user = (

        db.query(User)

        .filter(
            User.email == user_data.email
        )

        .first()

    )



    if not user:

        raise HTTPException(

            status_code=404,

            detail="User not found"

        )




    if not verify_password(

        user_data.password,

        user.password_hash

    ):


        raise HTTPException(

            status_code=400,

            detail="Invalid password"

        )





    access_token = create_access_token(

        data={

            "sub": user.email

        }

    )



    refresh_token = create_refresh_token(

        data={

            "sub": user.email

        }

    )



    refresh_obj = RefreshToken(

        user_id=user.id,

        token=refresh_token,

        expires_at=(

            datetime.utcnow()

            + timedelta(days=7)

        )

    )



    db.add(refresh_obj)

    db.commit()



    return {


        "access_token": access_token,


        "refresh_token": refresh_token,


        "token_type": "bearer",


        "expires_in": 3600

    }







# ============================================================
# FACEBOOK LOGIN START
# ============================================================
@router.get("/facebook/login")
def facebook_login():
    facebook_url = (
        "https://www.facebook.com/v20.0/dialog/oauth?"
        + urlencode({
            "client_id": settings.FACEBOOK_CLIENT_ID,
            "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
            "scope": "email,public_profile,pages_show_list,pages_read_engagement,pages_manage_posts",
            "auth_type": "rerequest",
            "response_type": "code"
        })
    )
    return RedirectResponse(url=facebook_url)


# ============================================================
# FACEBOOK CALLBACK
# ============================================================
@router.get("/facebook/callback")
def facebook_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    code = request.query_params.get("code")
    if code:
        code = code.split("#")[0].strip()

    frontend_url = getattr(settings, "FRONTEND_URL", "https://samrtautoposted.onrender.com").rstrip("/")

    if not code:
        return RedirectResponse(url=f"{frontend_url}/login?error=facebook_code_missing", status_code=302)

    # -----------------------------------------
    # 1. GET USER ACCESS TOKEN
    # -----------------------------------------
    token_response = requests.get(
        "https://graph.facebook.com/v20.0/oauth/access_token",
        params={
            "client_id": settings.FACEBOOK_CLIENT_ID,
            "client_secret": settings.FACEBOOK_CLIENT_SECRET,
            "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
            "code": code
        }
    )

    token_data = token_response.json()
    user_access_token = token_data.get("access_token")

    # Agar code expire/used ho chuka hai, raw JSON error na dikha kar login/dashboard par bhejein
    if not user_access_token:
        print("Facebook token error:", token_data)
        return RedirectResponse(url=f"{frontend_url}/login?error=code_already_used", status_code=302)

    # -----------------------------------------
    # 2. GET FACEBOOK USER DETAILS
    # -----------------------------------------
    user_response = requests.get(
        "https://graph.facebook.com/v20.0/me",
        params={
            "fields": "id,name,email,picture",
            "access_token": user_access_token
        }
    )
    facebook_user = user_response.json()
    facebook_id = facebook_user.get("id")
    name = facebook_user.get("name", "Facebook User")
    email = facebook_user.get("email") or f"{facebook_id}@facebook.local"

    picture = None
    if facebook_user.get("picture"):
        picture = facebook_user.get("picture", {}).get("data", {}).get("url")

    # -----------------------------------------
    # 3. GET FACEBOOK PAGES
    # -----------------------------------------
    pages_response = requests.get(
        "https://graph.facebook.com/v20.0/me/accounts",
        params={"access_token": user_access_token}
    )
    pages_data = pages_response.json()

    page_id = None
    page_access_token = None
    page_name = name

    if pages_data.get("data") and len(pages_data["data"]) > 0:
        page = pages_data["data"][0]
        page_id = page.get("id")
        page_access_token = page.get("access_token")
        page_name = page.get("name")

    # -----------------------------------------
    # 4. CREATE / UPDATE DB USER
    # -----------------------------------------
    user = db.query(User).filter(User.facebook_id == facebook_id).first()
    if not user:
        # Check by email as fallback
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.facebook_id = facebook_id
            user.auth_provider = "facebook"
        else:
            user = User(
                name=name,
                email=email,
                password_hash=None,
                facebook_id=facebook_id,
                profile_image=picture,
                auth_provider="facebook",
                is_verified=True,
                status="active",
                is_active=True
            )
            db.add(user)
    else:
        user.name = name
        user.profile_image = picture
        user.status = "active"

    db.commit()
    db.refresh(user)

    user_organization = get_or_create_personal_organization(db=db, user=user)

    # -----------------------------------------
    # 5. SAVE FACEBOOK SOCIAL ACCOUNT
    # -----------------------------------------
    if page_id and page_access_token:
        old_account = db.query(SocialAccount).filter(
            SocialAccount.organization_id == user_organization.id,
            SocialAccount.provider == "facebook",
            SocialAccount.page_id == page_id
        ).first()

        if not old_account:
            social_account = SocialAccount(
                organization_id=user_organization.id,
                provider="facebook",
                account_name=page_name,
                page_id=page_id,
                access_token=page_access_token,
                refresh_token=None,
                expires_at=None,
                is_active=True
            )
            db.add(social_account)
        else:
            old_account.access_token = page_access_token
            old_account.account_name = page_name

        db.commit()

    # -----------------------------------------
    # 6. GENERATE JWT & REDIRECT TO DASHBOARD
    # -----------------------------------------
    access_token = create_access_token(data={"sub": user.email})
    refresh_token_value = create_refresh_token(data={"sub": user.email})

    refresh_obj = RefreshToken(
        user_id=user.id,
        token=refresh_token_value,
        expires_at=datetime.utcnow() + timedelta(days=30),
        is_revoked=False
    )
    db.add(refresh_obj)
    db.commit()

    return RedirectResponse(
        url=f"{frontend_url}/dashboard?token={access_token}&refresh={refresh_token_value}",
        status_code=302
    )

# ============================================================
# INSTAGRAM LOGIN START
# ============================================================
# NOTE: there was previously a duplicate "/instagram/login" route
# defined further down in this file using the old, deprecated
# Instagram Basic Display flow (api.instagram.com). It has been
# removed - this is the only /instagram/login route now, and it
# uses the current Instagram Business Login flow.
# ============================================================

@router.get("/instagram/login")
def instagram_login():

    redirect_uri = settings.INSTAGRAM_REDIRECT_URI

    instagram_url = (
        "https://www.instagram.com/oauth/authorize?"
        + urlencode({

            "client_id": settings.INSTAGRAM_CLIENT_ID,

            "redirect_uri": redirect_uri,

            "scope":
            "instagram_business_basic,instagram_business_content_publish",

            "response_type":
            "code"

        })
    )


    print("==============================")
    print("INSTAGRAM LOGIN REDIRECT URI")
    print(redirect_uri)

    print("==============================")
    print("INSTAGRAM LOGIN URL")
    print(instagram_url)

    print("==============================")


    return RedirectResponse(
        url=instagram_url
    )


# ============================================================
# INSTAGRAM CALLBACK
# ============================================================
@router.get("/instagram/callback")
def instagram_callback(
    request: Request,
    db: Session = Depends(get_db)
):

    print("==============================")
    print("INSTAGRAM CALLBACK START")
    print("==============================")

    # -----------------------------------------
    # GET CODE
    # -----------------------------------------
    code = request.query_params.get("code")

    if code:
        code = code.split("#")[0].strip()

    print("CODE:")
    print(code)

    if not code:
        raise HTTPException(
            status_code=400,
            detail="Instagram code missing"
        )

    redirect_uri = settings.INSTAGRAM_REDIRECT_URI

    print("==============================")
    print("REDIRECT URI")
    print(redirect_uri)
    print("==============================")

    # ========================================================
    # GET ACCESS TOKEN
    # ========================================================
    token_response = requests.post(
        "https://api.instagram.com/oauth/access_token",
        data={
            "client_id": settings.INSTAGRAM_CLIENT_ID,
            "client_secret": settings.INSTAGRAM_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code": code
        }
    )

    token_data = token_response.json()

    print("==============================")
    print("INSTAGRAM TOKEN RESPONSE")
    print(token_data)
    print("==============================")

    if "access_token" not in token_data:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Instagram token failed",
                "response": token_data
            }
        )

    instagram_access_token = token_data.get("access_token")
    instagram_user_id = token_data.get("user_id")

    # ========================================================
    # GET INSTAGRAM USER
    # ========================================================
    user_response = requests.get(
        "https://graph.instagram.com/me",
        params={
            "fields": "id,username",
            "access_token": instagram_access_token
        }
    )

    instagram_user = user_response.json()

    print("==============================")
    print("INSTAGRAM USER")
    print(instagram_user)
    print("==============================")

    instagram_id = str(instagram_user.get("id") or instagram_user_id)
    username = instagram_user.get("username", f"instagram_{instagram_id}")

    # Valid email address to pass Pydantic EmailStr validation
    email = f"{instagram_id}@instagram.smartautopost.com"

    # ========================================================
    # CREATE / FIND USER
    # ========================================================
    user = (
        db.query(User)
        .filter(
            (User.instagram_id == instagram_id) | (User.email == email)
        )
        .first()
    )

    if not user:
        user = User(
            name=username,
            email=email,
            password_hash=None,
            instagram_id=instagram_id,
            auth_provider="instagram",
            is_verified=True,
            status="active",
            is_active=True
        )
        db.add(user)
    else:
        user.name = username
        user.email = email  # Updates old .local emails to valid format
        user.instagram_id = instagram_id
        user.auth_provider = "instagram"
        user.is_verified = True
        user.status = "active"
        user.is_active = True

    db.commit()
    db.refresh(user)

    # ========================================================
    # ENSURE USER HAS A PERSONAL ORGANIZATION
    # ========================================================
    user_organization = get_or_create_personal_organization(db=db, user=user)

    # ========================================================
    # EXCHANGE FOR LONG-LIVED TOKEN
    # ========================================================
    long_lived_token = instagram_access_token

    try:
        long_lived_response = requests.get(
            "https://graph.instagram.com/access_token",
            params={
                "grant_type": "ig_exchange_token",
                "client_secret": settings.INSTAGRAM_CLIENT_SECRET,
                "access_token": instagram_access_token,
            },
        )

        long_lived_data = long_lived_response.json()

        if "access_token" in long_lived_data:
            long_lived_token = long_lived_data["access_token"]

        print("==============================")
        print("INSTAGRAM LONG-LIVED TOKEN RESPONSE")
        print(long_lived_data)
        print("==============================")

    except Exception as error:
        print("Instagram long-lived token exchange failed:", error)

    # ========================================================
    # SAVE / UPDATE INSTAGRAM SOCIAL ACCOUNT
    # ========================================================
    existing_social_account = (
        db.query(SocialAccount)
        .filter(
            SocialAccount.provider == "instagram",
            SocialAccount.page_id == instagram_id,
        )
        .first()
    )

    if existing_social_account:
        existing_social_account.access_token = long_lived_token
        existing_social_account.account_name = username
        existing_social_account.is_active = True
        existing_social_account.organization_id = user_organization.id
        db.commit()
    else:
        social_account = SocialAccount(
            organization_id=user_organization.id,
            provider="instagram",
            account_name=username,
            page_id=instagram_id,
            instagram_id=instagram_id,
            access_token=long_lived_token,
            refresh_token=None,
            expires_at=None,
        )
        db.add(social_account)
        db.commit()

    print("==============================")
    print("INSTAGRAM TOKEN SAVED")
    print("==============================")

    # ========================================================
    # CREATE JWT TOKEN
    # ========================================================
    access_token = create_access_token(
        data={"sub": user.email}
    )

    refresh_token_value = create_refresh_token(
        data={"sub": user.email}
    )

    refresh_obj = RefreshToken(
        user_id=user.id,
        token=refresh_token_value,
        expires_at=(
            datetime.utcnow()
            +
            timedelta(days=30)
        ),
        is_revoked=False
    )

    db.add(refresh_obj)
    db.commit()

    print("==============================")
    print("INSTAGRAM LOGIN SUCCESS")
    print(user.id)
    print("==============================")

    return RedirectResponse(
        url=f"https://samrtautoposted.onrender.com/dashboard?token={access_token}&refresh={refresh_token_value}",
        status_code=302
    )

@router.get(
    "/me",
    response_model=UserResponse
)
def get_my_profile(

    current_user: User = Depends(
        get_current_user
    )

):

    return current_user





# ============================================================
# REFRESH TOKEN
# ============================================================


@router.post(
    "/refresh"
)
def refresh_access_token(

    request_data: RefreshTokenRequest,

    request: Request,

    db: Session = Depends(get_db),

):


    refresh_token = (

        db.query(RefreshToken)

        .filter(

            RefreshToken.token ==
            request_data.refresh_token,


            RefreshToken.expires_at >
            datetime.utcnow(),


            RefreshToken.is_revoked ==
            False

        )

        .first()

    )



    if not refresh_token:


        raise HTTPException(

            status_code=401,

            detail="Invalid or expired refresh token"

        )




    user = (

        db.query(User)

        .filter(
            User.id ==
            refresh_token.user_id
        )

        .first()

    )



    if not user:


        raise HTTPException(

            status_code=401,

            detail="User not found"

        )



    new_access_token = create_access_token(

        data={

            "sub":
            user.email

        }

    )



    new_refresh_token = create_refresh_token(

        data={

            "sub":
            user.email

        }

    )



    refresh_token.is_revoked = True



    new_refresh = RefreshToken(

        user_id=user.id,


        token=new_refresh_token,


        expires_at=(

            datetime.utcnow()

            + timedelta(days=7)

        )

    )



    db.add(new_refresh)

    db.commit()



    return {


        "access_token":
        new_access_token,


        "refresh_token":
        new_refresh_token,


        "token_type":
        "bearer"


    }







# ============================================================
# LOGOUT
# ============================================================



@router.post(
    "/logout"
)
def logout(

    request: Request,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(get_db)

):


    (

        db.query(RefreshToken)

        .filter(

            RefreshToken.user_id ==
            current_user.id

        )

        .update(

            {

                "is_revoked":
                True

            }

        )

    )



    db.commit()



    return {


        "success":
        True,


        "message":
        "Logout successful"

    }







# ============================================================
# VERIFY EMAIL
# ============================================================


@router.post(
    "/verify-email"
)
def verify_email(

    data: VerifyEmailRequest,

    request: Request,

    db: Session = Depends(get_db)

):


    user = (

        db.query(User)

        .filter(

            User.email_verification_token ==
            data.token

        )

        .first()

    )



    if not user:


        raise HTTPException(

            status_code=400,

            detail="Invalid token"

        )



    user.is_verified = True

    user.email_verification_token = None


    db.commit()



    return {


        "success":
        True,


        "message":
        "Email verified successfully"

    }







# ============================================================
# FORGOT PASSWORD
# ============================================================



@router.post(
    "/forgot-password"
)
def forgot_password(

    data: ForgotPasswordRequest,

    request: Request,

    db: Session = Depends(get_db)

):


    user = (

        db.query(User)

        .filter(
            User.email ==
            data.email
        )

        .first()

    )



    if not user:


        return {


            "success":
            True,


            "message":
            "Reset link sent if email exists"

        }



    token = secrets.token_urlsafe(32)



    user.password_reset_token = token


    user.password_reset_expires = (

        datetime.utcnow()

        + timedelta(hours=24)

    )


    db.commit()



    send_password_reset_email(

        user.email,

        token

    )



    return {


        "success":
        True,


        "message":
        "Password reset link sent"

    }







# ============================================================
# RESET PASSWORD
# ============================================================


@router.post(
    "/reset-password"
)
def reset_password(

    data: ResetPasswordRequest,

    request: Request,

    db: Session = Depends(get_db)

):


    user = (

        db.query(User)

        .filter(

            User.password_reset_token ==
            data.token,


            User.password_reset_expires >
            datetime.utcnow()

        )

        .first()

    )



    if not user:


        raise HTTPException(

            status_code=400,

            detail="Invalid or expired token"

        )



    user.password_hash = hash_password(

        data.new_password

    )


    user.password_reset_token = None

    user.password_reset_expires = None



    db.commit()



    return {


        "success":
        True,


        "message":
        "Password reset successfully"

    }
    
# ============================================================
# ENABLE TWO FACTOR AUTHENTICATION
# ============================================================


@router.post(
    "/2fa/enable"
)
def enable_2fa(

    request: Request,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(get_db)

):

    import pyotp


    secret = pyotp.random_base32()


    current_user.two_factor_secret = secret


    db.commit()



    provisioning_uri = (

        pyotp.TOTP(secret)

        .provisioning_uri(

            name=current_user.email,

            issuer_name="SmartAutoPost"

        )

    )


    return {


        "success":
        True,


        "secret":
        secret,


        "qr_code":

        (
            "https://api.qrserver.com/v1/"
            "create-qr-code/"
            f"?data={provisioning_uri}"
        )

    }







# ============================================================
# VERIFY TWO FACTOR AUTHENTICATION
# ============================================================



@router.post(
    "/2fa/verify"
)
def verify_2fa(

    data: TwoFactorRequest,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(get_db)

):

    import pyotp



    if not current_user.two_factor_secret:


        raise HTTPException(

            status_code=400,

            detail="2FA not setup"

        )



    totp = pyotp.TOTP(

        current_user.two_factor_secret

    )



    if not totp.verify(data.otp):


        raise HTTPException(

            status_code=400,

            detail="Invalid OTP"

        )



    current_user.two_factor_enabled = True


    db.commit()



    return {


        "success":
        True,


        "message":
        "2FA enabled successfully"

    }







# ============================================================
# LINKEDIN LOGIN START
# ============================================================


@router.get(
    "/linkedin/login"
)
def linkedin_login():

    linkedin_url = (

        "https://www.linkedin.com/oauth/v2/authorization?"

        + urlencode(

            {

                "response_type":
                "code",


                "client_id":
                settings.LINKEDIN_CLIENT_ID,


                "redirect_uri":
                settings.LINKEDIN_REDIRECT_URI,


                # "openid profile email" se sirf LOGIN hota hai.
                # "w_member_social" ke bina POSTING kabhi kaam
                # nahi karegi -- ye scope tabhi milega jab
                # LinkedIn Developer Portal me apni app ke
                # "Products" tab me "Share on LinkedIn" add karke
                # LinkedIn se approval liya ho.
                "scope":
                "openid profile email w_member_social",

            }

        )

    )

    # Pehle ye endpoint sirf JSON {"url": ...} return karta tha,
    # isliye login.html ka <a href="/api/v1/auth/linkedin/login">
    # button click karne par sirf raw JSON dikhta tha, LinkedIn
    # par navigate hi nahi hota tha. Ab real redirect hai.
    return RedirectResponse(url=linkedin_url)


# ============================================================
# LINKEDIN CALLBACK
# ============================================================

@router.get("/linkedin/callback")
def linkedin_callback(
    request: Request,
    db: Session = Depends(get_db),
):

    code = request.query_params.get("code")
    error = request.query_params.get("error")

    if error:
        raise HTTPException(
            status_code=400,
            detail=f"LinkedIn login cancelled or failed: {error}",
        )

    if not code:
        raise HTTPException(
            status_code=400,
            detail="LinkedIn authorization code missing",
        )

    # --------------------------------------------------
    # STEP 1: EXCHANGE CODE FOR ACCESS TOKEN
    # --------------------------------------------------
    token_response = requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "client_secret": settings.LINKEDIN_CLIENT_SECRET,
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        },
    )

    token_data = token_response.json()

    print("==============================")
    print("LINKEDIN TOKEN RESPONSE")
    print(token_data)
    print("==============================")

    if "access_token" not in token_data:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "LinkedIn token exchange failed",
                "response": token_data,
            },
        )

    linkedin_access_token = token_data["access_token"]

    # --------------------------------------------------
    # STEP 2: GET LINKEDIN PROFILE (OpenID Connect userinfo)
    # --------------------------------------------------
    profile_response = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={
            "Authorization": f"Bearer {linkedin_access_token}"
        },
    )

    profile = profile_response.json()

    print("==============================")
    print("LINKEDIN PROFILE")
    print(profile)
    print("==============================")

    linkedin_member_id = profile.get("sub")
    full_name = profile.get("name", "LinkedIn User")
    linkedin_email = profile.get(
        "email",
        f"{linkedin_member_id}@linkedin.local",
    )

    if not linkedin_member_id:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "LinkedIn profile fetch failed",
                "response": profile,
            },
        )

    # --------------------------------------------------
    # STEP 3: CREATE / FIND USER
    # --------------------------------------------------
    user = (
        db.query(User)
        .filter(User.email == linkedin_email)
        .first()
    )

    if not user:
        user = User(
            name=full_name,
            email=linkedin_email,
            password_hash=None,
            auth_provider="linkedin",
            role="user",
            is_verified=True,
            status="active",
            is_active=True,
        )
        db.add(user)
    else:
        user.name = full_name
        user.auth_provider = "linkedin"
        user.is_verified = True
        user.status = "active"

    db.commit()
    db.refresh(user)

    # --------------------------------------------------
    # STEP 4: ENSURE USER HAS A PERSONAL ORGANIZATION
    # --------------------------------------------------
    user_organization = get_or_create_personal_organization(
        db=db, user=user
    )

    # --------------------------------------------------
    # STEP 5: SAVE / UPDATE LINKEDIN SOCIAL ACCOUNT
    # --------------------------------------------------
    # page_id yahan LinkedIn member URN store karta hai
    # ("urn:li:person:{id}") -- posting ke waqt "author" field
    # me yahi chahiye hota hai.
    author_urn = f"urn:li:person:{linkedin_member_id}"

    existing_social_account = (
        db.query(SocialAccount)
        .filter(
            SocialAccount.provider == "linkedin",
            SocialAccount.page_id == author_urn,
        )
        .first()
    )

    if existing_social_account:
        existing_social_account.access_token = linkedin_access_token
        existing_social_account.account_name = full_name
        existing_social_account.is_active = True
        existing_social_account.organization_id = user_organization.id
        db.commit()
    else:
        social_account = SocialAccount(
            organization_id=user_organization.id,
            provider="linkedin",
            account_name=full_name,
            page_id=author_urn,
            access_token=linkedin_access_token,
            refresh_token=None,
            expires_at=None,
        )
        db.add(social_account)
        db.commit()

    # --------------------------------------------------
    # STEP 6: CREATE JWT
    # --------------------------------------------------
    access_token = create_access_token(data={"sub": user.email})
    refresh_token_value = create_refresh_token(data={"sub": user.email})

    refresh_obj = RefreshToken(
        user_id=user.id,
        token=refresh_token_value,
        expires_at=datetime.utcnow()
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        is_revoked=False,
    )

    db.add(refresh_obj)
    db.commit()

    print("==============================")
    print("LINKEDIN LOGIN SUCCESS")
    print(user.id)
    print("==============================")

    return RedirectResponse(
        url=(
            f"/dashboard?token={access_token}"
            f"&refresh={refresh_token_value}&provider=linkedin"
        ),
        status_code=302,
    )
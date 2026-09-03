from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Request,
    Response,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
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
from app.services.audit_log_service import AuditLogService
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from app.dependencies.auth import get_current_user
from app.core.config import settings


try:
    from app.services.email import (
        send_verification_email,
        send_password_reset_email,
    )
except ImportError:
    def send_verification_email(to_email, token):
        print(f"Verification email: {to_email} {token}")

    def send_password_reset_email(to_email, token):
        print(f"Reset email: {to_email} {token}")


router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


def get_frontend_url(request: Request) -> str:
    """Dynamic Host Capture taaki smartautopost aur samrtautoposted dono handle ho sakein"""
    forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    proto = request.headers.get("x-forwarded-proto", "https")
    if forwarded_host:
        return f"{proto}://{forwarded_host}".rstrip("/")
    return getattr(settings, "FRONTEND_URL", "https://samrtautoposted.onrender.com").rstrip("/")


def get_or_create_personal_organization(db: Session, user: User) -> Organization:
    existing_member = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id, OrganizationMember.role == "owner")
        .first()
    )
    if existing_member:
        org = db.query(Organization).filter(Organization.id == existing_member.organization_id).first()
        if org:
            return org

    base_slug = (
        (user.name or user.email or f"user-{user.id}")
        .lower().strip().replace(" ", "-").replace("@", "-").replace(".", "-")
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
                user_agent=request.headers.get("user-agent"),
                details=details,
            )
        )
    except Exception as error:
        db.rollback()
        print(f"Audit log error: {error}")


# =========================================================
# EMAIL & PASSWORD AUTH
# =========================================================

@router.post("/register", response_model=UserResponse)
def register_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    email_clean = user_data.email.lower().strip()
    existing_user = (
        db.query(User)
        .filter(User.email == email_clean)
        .first()
    )

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(user_data.password)

    new_user = User(
        name=user_data.name,
        email=email_clean,
        password_hash=hashed_password,
        role="user",
        is_verified=True,
        status="active",
        is_active=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    get_or_create_personal_organization(db=db, user=new_user)

    create_auth_audit_log(
        db=db,
        request=request,
        user_id=new_user.id,
        entity_id=new_user.id,
        action="user_registered",
        details={"email": new_user.email, "name": new_user.name}
    )

    return new_user


@router.post("/login")
def login_user(
    user_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
):
    email_clean = user_data.email.lower().strip()
    user = db.query(User).filter(User.email == email_clean).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid password")

    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})

    refresh_obj = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )

    db.add(refresh_obj)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 3600
    }


# =========================================================
# GET ALL CONNECTED SOCIAL ACCOUNTS (FOR DROPDOWN)
# =========================================================

@router.get("/connected-accounts")
def get_connected_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Dropdown me dikhane ke liye user ke sabhi active accounts layega"""
    user_org = get_or_create_personal_organization(db=db, user=current_user)
    
    accounts = (
        db.query(SocialAccount)
        .filter(
            SocialAccount.organization_id == user_org.id,
            SocialAccount.is_active == True
        )
        .all()
    )

    result = []
    for acc in accounts:
        result.append({
            "id": acc.id,
            "provider": acc.provider,
            "account_name": acc.account_name,
            "page_id": acc.page_id,
            "label": f"[{acc.provider.upper()}] {acc.account_name}"
        })

    return {"status": "success", "accounts": result}


# =========================================================
# FACEBOOK OAUTH
# =========================================================

@router.get("/facebook/login")
def facebook_login(user_id: int | None = None):
    scopes = [
        "email",
        "public_profile",
        "pages_show_list",
        "pages_read_engagement",
        "pages_manage_posts"
    ]
    state_payload = f"user_{user_id}" if user_id else "direct"
    facebook_url = (
        "https://www.facebook.com/v20.0/dialog/oauth?"
        + urlencode({
            "client_id": settings.FACEBOOK_CLIENT_ID,
            "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
            "scope": ",".join(scopes),
            "auth_type": "rerequest",
            "response_type": "code",
            "state": state_payload
        })
    )
    return RedirectResponse(url=facebook_url)


@router.get("/facebook/callback")
def facebook_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    user_agent = request.headers.get("user-agent", "").lower()
    if "facebookexternalhit" in user_agent or "meta-externalagent" in user_agent or "bot" in user_agent:
        return Response(status_code=200)

    code = request.query_params.get("code")
    state = request.query_params.get("state")
    if code:
        code = code.split("#")[0].strip()

    frontend_url = get_frontend_url(request)

    if not code:
        return RedirectResponse(url=f"{frontend_url}/login?error=facebook_code_missing", status_code=302)

    token_response = requests.get(
        "https://graph.facebook.com/v20.0/oauth/access_token",
        params={
            "client_id": settings.FACEBOOK_CLIENT_ID,
            "client_secret": settings.FACEBOOK_CLIENT_SECRET,
            "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
            "code": code
        },
        timeout=15
    )

    token_data = token_response.json()
    user_access_token = token_data.get("access_token")

    if not user_access_token:
        return RedirectResponse(url=f"{frontend_url}/login?error=auth_failed", status_code=302)

    user_response = requests.get(
        "https://graph.facebook.com/v20.0/me",
        params={"fields": "id,name,email,picture", "access_token": user_access_token},
        timeout=15
    )
    facebook_user = user_response.json()
    facebook_id = facebook_user.get("id")
    name = facebook_user.get("name", "Facebook User")
    email = (facebook_user.get("email") or f"{facebook_id}@facebook.com").lower().strip()

    picture = None
    if facebook_user.get("picture"):
        picture = facebook_user.get("picture", {}).get("data", {}).get("url")

    # Match existing user agar logged in user_id state me aaya ho
    target_user_id = int(state.replace("user_", "")) if (state and state.startswith("user_")) else None
    user = None
    if target_user_id:
        user = db.query(User).filter(User.id == target_user_id).first()

    if not user:
        user = db.query(User).filter(User.facebook_id == facebook_id).first()
    if not user:
        user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(
            name=name,
            email=email,
            password_hash=None,
            facebook_id=facebook_id,
            profile_image=picture,
            auth_provider="facebook",
            role="user",
            is_verified=True,
            status="active",
            is_active=True
        )
        db.add(user)
    else:
        if not user.facebook_id:
            user.facebook_id = facebook_id
        user.name = name or user.name
        user.status = "active"

    db.commit()
    db.refresh(user)

    user_organization = get_or_create_personal_organization(db=db, user=user)

    # Pages fetch & store
    pages_response = requests.get(
        "https://graph.facebook.com/v20.0/me/accounts",
        params={"access_token": user_access_token},
        timeout=15
    )
    pages_data = pages_response.json()
    page_list = pages_data.get("data", [])

    if page_list:
        for p in page_list:
            p_id = str(p.get("id"))
            p_token = p.get("access_token")
            p_name = p.get("name", "Facebook Page")

            existing_acc = db.query(SocialAccount).filter(
                SocialAccount.organization_id == user_organization.id,
                SocialAccount.provider == "facebook",
                SocialAccount.page_id == p_id
            ).first()

            if not existing_acc:
                new_acc = SocialAccount(
                    organization_id=user_organization.id,
                    provider="facebook",
                    account_name=p_name,
                    page_id=p_id,
                    access_token=p_token,
                    refresh_token=None,
                    expires_at=None,
                    is_active=True
                )
                db.add(new_acc)
            else:
                existing_acc.access_token = p_token
                existing_acc.account_name = p_name
                existing_acc.is_active = True

        db.commit()

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
        url=f"{frontend_url}/dashboard?token={access_token}&refresh={refresh_token_value}&provider=facebook&platform=facebook",
        status_code=302
    )


# =========================================================
# INSTAGRAM OAUTH
# =========================================================

@router.get("/instagram/login")
def instagram_login(user_id: int | None = None):
    redirect_uri = settings.INSTAGRAM_REDIRECT_URI
    state_payload = f"user_{user_id}" if user_id else "direct"

    instagram_url = (
        "https://www.instagram.com/oauth/authorize?"
        + urlencode({
            "client_id": settings.INSTAGRAM_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "scope": "instagram_business_basic,instagram_business_content_publish",
            "response_type": "code",
            "state": state_payload
        })
    )

    return RedirectResponse(url=instagram_url)


@router.get("/instagram/callback")
def instagram_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    if code:
        code = code.split("#")[0].strip()

    frontend_url = get_frontend_url(request)

    if not code:
        raise HTTPException(status_code=400, detail="Instagram code missing")

    redirect_uri = settings.INSTAGRAM_REDIRECT_URI

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

    if "access_token" not in token_data:
        raise HTTPException(
            status_code=400,
            detail={"message": "Instagram token failed", "response": token_data}
        )

    instagram_access_token = token_data.get("access_token")
    instagram_user_id = token_data.get("user_id")

    user_response = requests.get(
        "https://graph.instagram.com/me",
        params={"fields": "id,username", "access_token": instagram_access_token}
    )

    instagram_user = user_response.json()
    instagram_id = str(instagram_user.get("id") or instagram_user_id)
    username = instagram_user.get("username", f"instagram_{instagram_id}")
    email = f"{instagram_id}@instagram.smartautopost.com"

    # Match User
    target_user_id = int(state.replace("user_", "")) if (state and state.startswith("user_")) else None
    user = None
    if target_user_id:
        user = db.query(User).filter(User.id == target_user_id).first()

    if not user:
        user = (
            db.query(User)
            .filter((User.instagram_id == instagram_id) | (User.email == email))
            .first()
        )

    if not user:
        user = User(
            name=username,
            email=email,
            password_hash=None,
            instagram_id=instagram_id,
            auth_provider="instagram",
            role="user",
            is_verified=True,
            status="active",
            is_active=True
        )
        db.add(user)
    else:
        user.instagram_id = instagram_id
        user.is_active = True

    db.commit()
    db.refresh(user)

    user_organization = get_or_create_personal_organization(db=db, user=user)

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
    except Exception as error:
        print("Instagram long-lived token exchange failed:", error)

    existing_social_account = (
        db.query(SocialAccount)
        .filter(
            SocialAccount.organization_id == user_organization.id,
            SocialAccount.provider == "instagram",
            SocialAccount.page_id == instagram_id,
        )
        .first()
    )

    if existing_social_account:
        existing_social_account.access_token = long_lived_token
        existing_social_account.account_name = username
        existing_social_account.is_active = True
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
            is_active=True
        )
        db.add(social_account)

    db.commit()

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
        url=f"{frontend_url}/dashboard?token={access_token}&refresh={refresh_token_value}&provider=instagram&platform=instagram",
        status_code=302
    )


# =========================================================
# LINKEDIN OAUTH
# =========================================================

@router.get("/linkedin/login")
def linkedin_login(user_id: int | None = None):
    state_payload = f"user_{user_id}" if user_id else "direct"
    linkedin_url = (
        "https://www.linkedin.com/oauth/v2/authorization?"
        + urlencode({
            "response_type": "code",
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
            "scope": "openid profile email w_member_social",
            "state": state_payload
        })
    )
    return RedirectResponse(url=linkedin_url)


@router.get("/linkedin/callback")
def linkedin_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    code = request.query_params.get("code")
    error = request.query_params.get("error")
    state = request.query_params.get("state")
    frontend_url = get_frontend_url(request)

    if error:
        raise HTTPException(status_code=400, detail=f"LinkedIn login cancelled or failed: {error}")

    if not code:
        raise HTTPException(status_code=400, detail="LinkedIn authorization code missing")

    token_response = requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "client_secret": settings.LINKEDIN_CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    token_data = token_response.json()

    if "access_token" not in token_data:
        raise HTTPException(
            status_code=400,
            detail={"message": "LinkedIn token exchange failed", "response": token_data}
        )

    linkedin_access_token = token_data["access_token"]

    profile_response = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": f"Bearer {linkedin_access_token}"},
    )

    profile = profile_response.json()
    linkedin_member_id = profile.get("sub")
    full_name = profile.get("name", "LinkedIn User")
    linkedin_email = (profile.get("email") or f"{linkedin_member_id}@linkedin.local").lower().strip()

    if not linkedin_member_id:
        raise HTTPException(
            status_code=400,
            detail={"message": "LinkedIn profile fetch failed", "response": profile}
        )

    target_user_id = int(state.replace("user_", "")) if (state and state.startswith("user_")) else None
    user = None
    if target_user_id:
        user = db.query(User).filter(User.id == target_user_id).first()

    if not user:
        user = db.query(User).filter(User.email == linkedin_email).first()

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
        user.is_active = True

    db.commit()
    db.refresh(user)

    user_organization = get_or_create_personal_organization(db=db, user=user)

    author_urn = f"urn:li:person:{linkedin_member_id}"

    existing_social_account = (
        db.query(SocialAccount)
        .filter(
            SocialAccount.organization_id == user_organization.id,
            SocialAccount.provider == "linkedin",
            SocialAccount.page_id == author_urn,
        )
        .first()
    )

    if existing_social_account:
        existing_social_account.access_token = linkedin_access_token
        existing_social_account.account_name = full_name
        existing_social_account.is_active = True
    else:
        social_account = SocialAccount(
            organization_id=user_organization.id,
            provider="linkedin",
            account_name=full_name,
            page_id=author_urn,
            access_token=linkedin_access_token,
            refresh_token=None,
            expires_at=None,
            is_active=True
        )
        db.add(social_account)

    db.commit()

    access_token = create_access_token(data={"sub": user.email})
    refresh_token_value = create_refresh_token(data={"sub": user.email})

    refresh_obj = RefreshToken(
        user_id=user.id,
        token=refresh_token_value,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        is_revoked=False,
    )
    db.add(refresh_obj)
    db.commit()

    return RedirectResponse(
        url=f"{frontend_url}/dashboard?token={access_token}&refresh={refresh_token_value}&provider=linkedin&platform=linkedin",
        status_code=302,
    )


# =========================================================
# GOOGLE BUSINESS PROFILE (GMB) OAUTH
# =========================================================

@router.get("/google/login")
def google_login(request: Request, user_id: int | None = None):
    state_data = f"user_{user_id}" if user_id else "direct_login"
    
    scopes = [
        "openid",
        "email",
        "profile",
        "https://www.googleapis.com/auth/business.manage",
    ]
    
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        + urlencode({
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(scopes),
            "access_type": "offline",
            "prompt": "consent",
            "state": state_data
        })
    )
    return RedirectResponse(url=google_auth_url)


@router.get("/google/callback")
def google_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    code = request.query_params.get("code")
    error = request.query_params.get("error")
    state = request.query_params.get("state")
    
    frontend_url = get_frontend_url(request)
    
    if error or not code:
        return RedirectResponse(url=f"{frontend_url}/social-accounts?error=google_auth_failed", status_code=302)

    # 1. Exchange Code
    token_response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15
    )
    
    token_data = token_response.json()
    google_access_token = token_data.get("access_token")
    google_refresh_token = token_data.get("refresh_token")

    if not google_access_token:
        return RedirectResponse(url=f"{frontend_url}/social-accounts?error=token_exchange_failed", status_code=302)

    # 2. Get Profile Info
    userinfo_res = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {google_access_token}"},
        timeout=15
    )
    google_profile = userinfo_res.json()
    google_id = google_profile.get("id")
    email = (google_profile.get("email") or "").lower().strip()
    name = google_profile.get("name", "Google Business User")

    # 3. User & Organization Mapping
    target_user_id = int(state.replace("user_", "")) if (state and state.startswith("user_")) else None
    user = None
    if target_user_id:
        user = db.query(User).filter(User.id == target_user_id).first()

    if not user:
        user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(
            name=name,
            email=email,
            password_hash=None,
            auth_provider="google",
            role="user",
            is_verified=True,
            status="active",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    target_org = get_or_create_personal_organization(db=db, user=user)

    # 4. Fetch GMB Accounts & Locations
    gmb_account_name = name
    gmb_account_id = None
    gmb_location_id = None

    try:
        acc_res = requests.get(
            "https://mybusinessaccountmanagement.googleapis.com/v1/accounts",
            headers={"Authorization": f"Bearer {google_access_token}"},
            timeout=15
        )
        accounts_data = acc_res.json()
        accounts_list = accounts_data.get("accounts", [])
        
        if accounts_list:
            gmb_account_id = accounts_list[0].get("name")
            gmb_account_name = accounts_list[0].get("accountName", name)
            
            loc_res = requests.get(
                f"https://mybusinessbusinessinformation.googleapis.com/v1/{gmb_account_id}/locations?readMask=name,title",
                headers={"Authorization": f"Bearer {google_access_token}"},
                timeout=15
            )
            loc_data = loc_res.json()
            locations_list = loc_data.get("locations", [])
            if locations_list:
                gmb_location_id = locations_list[0].get("name")
                gmb_account_name = locations_list[0].get("title", gmb_account_name)
    except Exception as gmb_err:
        print(f"Auto-fetch GMB locations error: {gmb_err}")

    # 5. Save/Update in SocialAccount
    page_target_id = gmb_location_id or gmb_account_id or google_id
    existing_social = db.query(SocialAccount).filter(
        SocialAccount.organization_id == target_org.id,
        SocialAccount.provider == "google_business",
        SocialAccount.page_id == page_target_id
    ).first()

    if not existing_social:
        new_social = SocialAccount(
            organization_id=target_org.id,
            provider="google_business",
            account_name=gmb_account_name,
            page_id=page_target_id,
            access_token=google_access_token,
            refresh_token=google_refresh_token,
            is_active=True
        )
        db.add(new_social)
    else:
        existing_social.account_name = gmb_account_name
        existing_social.access_token = google_access_token
        if google_refresh_token:
            existing_social.refresh_token = google_refresh_token
        existing_social.is_active = True

    db.commit()

    # 6. Return JWT Token
    access_token = create_access_token(data={"sub": user.email})
    refresh_token_value = create_refresh_token(data={"sub": user.email})

    refresh_obj = RefreshToken(
        user_id=user.id,
        token=refresh_token_value,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        is_revoked=False
    )
    db.add(refresh_obj)
    db.commit()

    return RedirectResponse(
        url=f"{frontend_url}/dashboard?token={access_token}&refresh={refresh_token_value}&provider=google&platform=google_business",
        status_code=302
    )


# =========================================================
# PROFILE, 2FA, TOKENS & UTILITIES
# =========================================================

@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/refresh")
def refresh_access_token(
    request_data: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    refresh_token = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token == request_data.refresh_token,
            RefreshToken.expires_at > datetime.utcnow(),
            RefreshToken.is_revoked == False
        )
        .first()
    )

    if not refresh_token:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = db.query(User).filter(User.id == refresh_token.user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    new_access_token = create_access_token(data={"sub": user.email})
    new_refresh_token = create_refresh_token(data={"sub": user.email})

    refresh_token.is_revoked = True

    new_refresh = RefreshToken(
        user_id=user.id,
        token=new_refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )

    db.add(new_refresh)
    db.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.post("/logout")
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    (
        db.query(RefreshToken)
        .filter(RefreshToken.user_id == current_user.id)
        .update({"is_revoked": True})
    )
    db.commit()

    return {"success": True, "message": "Logout successful"}


@router.post("/verify-email")
def verify_email(
    data: VerifyEmailRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email_verification_token == data.token).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")

    user.is_verified = True
    user.email_verification_token = None
    db.commit()

    return {"success": True, "message": "Email verified successfully"}


@router.post("/forgot-password")
def forgot_password(
    data: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == data.email.lower().strip()).first()

    if not user:
        return {"success": True, "message": "Reset link sent if email exists"}

    token = secrets.token_urlsafe(32)
    user.password_reset_token = token
    user.password_reset_expires = datetime.utcnow() + timedelta(hours=24)
    db.commit()

    send_password_reset_email(user.email, token)

    return {"success": True, "message": "Password reset link sent"}


@router.post("/reset-password")
def reset_password(
    data: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(
            User.password_reset_token == data.token,
            User.password_reset_expires > datetime.utcnow()
        )
        .first()
    )

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user.password_hash = hash_password(data.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    db.commit()

    return {"success": True, "message": "Reset password successfully"}


@router.post("/2fa/enable")
def enable_2fa(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    import pyotp
    secret = pyotp.random_base32()
    current_user.two_factor_secret = secret
    db.commit()

    provisioning_uri = pyotp.TOTP(secret).provisioning_uri(
        name=current_user.email,
        issuer_name="SmartAutoPost"
    )

    return {
        "success": True,
        "secret": secret,
        "qr_code": f"https://api.qrserver.com/v1/create-qr-code/?data={provisioning_uri}"
    }


@router.post("/2fa/verify")
def verify_2fa(
    data: TwoFactorRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    import pyotp
    if not current_user.two_factor_secret:
        raise HTTPException(status_code=400, detail="2FA not setup")

    totp = pyotp.TOTP(current_user.two_factor_secret)
    if not totp.verify(data.otp):
        raise HTTPException(status_code=400, detail="Invalid OTP")

    current_user.two_factor_enabled = True
    db.commit()

    return {"success": True, "message": "2FA enabled successfully"}
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates


router = APIRouter(tags=["Web UI"])


# Project kisi bhi working directory se run ho,
# templates ka absolute path correct milega.
BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates"),
)


PAGES = {
    "dashboard": (
        "Dashboard",
        "dashboard.html",
    ),
    "create-post": (
        "Create Post",
        "create_post.html",
    ),
    "posts": (
        "Posts",
        "posts.html",
    ),
    "ai-content": (
        "AI Content Studio",
        "ai_content.html",
    ),
    "calendar": (
        "Content Calendar",
        "calendar.html",
    ),
    "analytics": (
        "Analytics",
        "analytics.html",
    ),
    "post-analytics": (
        "Post Analytics",
        "post_analytics.html",
    ),
    "social-accounts": (
        "Connected Accounts",
        "social_accounts.html",
    ),
    "media-library": (
        "Media Library",
        "media_library.html",
    ),
    "brand-kit": (
        "Brand Kit",
        "brand_kit.html",
    ),
    "competitors": (
        "Competitors",
        "competitors.html",
    ),
    "clients": (
        "Clients & Team",
        "clients.html",
    ),
    "organizations": (
        "Organizations",
        "organizations.html",
    ),
    "roles": (
        "Roles & Permissions",
        "roles.html",
    ),
    "billing": (
        "Billing Overview",
        "billing.html",
    ),
    "plans": (
        "Plans",
        "plans.html",
    ),
    "subscriptions": (
        "Subscriptions",
        "subscriptions.html",
    ),
    "payments": (
        "Payments",
        "payments.html",
    ),
    "invoices": (
        "Invoices",
        "invoices.html",
    ),
    "refunds": (
        "Refunds",
        "refunds.html",
    ),
    "coupons": (
        "Coupons",
        "coupons.html",
    ),
    "usage": (
        "Usage",
        "usage.html",
    ),
    "notifications": (
        "Notifications",
        "notifications.html",
    ),
    "audit-logs": (
        "Audit Logs",
        "audit_logs.html",
    ),
    "profile": (
        "Profile",
        "profile.html",
    ),
    "settings": (
        "Settings",
        "settings.html",
    ),
    "api-status": (
        "API Status",
        "api_status.html",
    ),
    "help": (
        "Help & Setup",
        "help.html",
    ),
}


@router.get(
    "/",
    include_in_schema=False,
)
def web_root():
    return RedirectResponse(
        url="/login",
        status_code=302,
    )


@router.get(
    "/login",
    include_in_schema=False,
)
def login_page(
    request: Request,
):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "title": "Login",
            "page": "login",
        },
    )


@router.get(
    "/register",
    include_in_schema=False,
)
def register_page(
    request: Request,
):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={
            "title": "Register",
            "page": "register",
        },
    )


@router.get(
    "/forgot-password",
    include_in_schema=False,
)
def forgot_page(
    request: Request,
):
    return templates.TemplateResponse(
        request=request,
        name="forgot_password.html",
        context={
            "title": "Forgot Password",
            "page": "forgot-password",
        },
    )


@router.get(
    "/reset-password",
    include_in_schema=False,
)
def reset_page(
    request: Request,
):
    return templates.TemplateResponse(
        request=request,
        name="reset_password.html",
        context={
            "title": "Reset Password",
            "page": "reset-password",
        },
    )


@router.get(
    "/favicon.ico",
    include_in_schema=False,
)
def favicon():
    return RedirectResponse(
        url="/static/favicon.ico",
        status_code=307,
    )


@router.get(
    "/{page_name}",
    include_in_schema=False,
)
def app_page(
    page_name: str,
    request: Request,
):
    page_config = PAGES.get(page_name)

    if page_config is None:
        return templates.TemplateResponse(
            request=request,
            name="404.html",
            context={
                "title": "Not Found",
                "page": "404",
                "requested_page": page_name,
            },
            status_code=404,
        )

    title, template_name = page_config

    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context={
            "title": title,
            "page": page_name,
        },
    )
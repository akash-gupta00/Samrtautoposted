import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.database.base import Base
from app.database.session import engine

# =====================================================
# API ROUTERS
# =====================================================
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.organization import router as organization_router
from app.api.organization_member import router as organization_member_router
from app.api.social_account import router as social_account_router
from app.api.post import router as post_router
from app.api.media import router as media_router
from app.api.post_schedule import router as post_schedule_router

from app.api.ai_caption import router as ai_caption_router
from app.api.ai_hashtag import router as ai_hashtag_router
from app.api.ai_image_prompt import router as ai_image_prompt_router
from app.api.ai_seo import router as ai_seo_router
from app.api.gemini import router as gemini_router

from app.api.publishing import router as publishing_router
from app.api.dashboard import router as dashboard_router
from app.api.calendar import router as calendar_router
from app.api.analytics import router as analytics_router
from app.api.notification import router as notification_router

from app.api.plan import router as plan_router
from app.api.subscription import router as subscription_router
from app.api.payment import router as payment_router
from app.api.usage import router as usage_router
from app.api.invoice import router as invoice_router

from app.api.refund import router as refund_router
from app.api.coupon import router as coupon_router
from app.api.audit_log import router as audit_log_router
from app.api.competitor import router as competitor_router
from app.api.competitor_metric import router as competitor_metric_router
from app.api.post_analytic import router as post_analytic_router
from app.api.brand_kit import router as brand_kit_router
from app.api.role import router as role_router
from app.api.permission import router as permission_router
from app.api.member_role import router as member_role_router
from app.api.web import router as web_router

# Scheduler
from app.scheduler.post_scheduler import (
    start_scheduler,
    stop_scheduler,
)

# =====================================================
# APP CREATE
# =====================================================
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
)

# =====================================================
# CORS MIDDLEWARE
# =====================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# DATABASE INIT & AUTO-MIGRATION
# =====================================================
Base.metadata.create_all(bind=engine)

def run_auto_migrations():
    """Missing columns aur tables ko startup par automatic create/alter karega"""
    try:
        with engine.connect() as conn:
            # 1. Posts table columns
            conn.execute(text("ALTER TABLE posts ADD COLUMN IF NOT EXISTS platform_post_id VARCHAR(255);"))
            conn.execute(text("ALTER TABLE posts ADD COLUMN IF NOT EXISTS media_url TEXT;"))
            conn.execute(text("ALTER TABLE posts ADD COLUMN IF NOT EXISTS image_url TEXT;"))
            
            # 2. Analytics table ensure karein
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS analytics_records (
                    id SERIAL PRIMARY KEY,
                    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
                    likes INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    impressions INTEGER DEFAULT 0,
                    reach INTEGER DEFAULT 0,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
                );
            """))
            conn.commit()
            print("Auto-migration: Database schema verified and updated successfully!")
    except Exception as e:
        print(f"Auto-migration info: {e}")

# =====================================================
# START / STOP EVENTS
# =====================================================
@app.on_event("startup")
def startup_event():
    run_auto_migrations()
    start_scheduler()

@app.on_event("shutdown")
def shutdown_event():
    stop_scheduler()

# =====================================================
# API PREFIX & ROUTERS INCLUSION
# =====================================================
API_PREFIX = settings.API_V1_PREFIX

app.include_router(health_router, prefix=API_PREFIX)
app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(organization_router, prefix=API_PREFIX)
app.include_router(organization_member_router, prefix=API_PREFIX)
app.include_router(social_account_router, prefix=API_PREFIX)
app.include_router(post_router, prefix=API_PREFIX)
app.include_router(media_router, prefix=API_PREFIX)
app.include_router(post_schedule_router, prefix=API_PREFIX)

app.include_router(ai_caption_router, prefix=API_PREFIX)
app.include_router(ai_hashtag_router, prefix=API_PREFIX)
app.include_router(ai_image_prompt_router, prefix=API_PREFIX)
app.include_router(ai_seo_router, prefix=API_PREFIX)
app.include_router(gemini_router, prefix=API_PREFIX)

app.include_router(publishing_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(calendar_router, prefix=API_PREFIX)
app.include_router(analytics_router, prefix=API_PREFIX)
app.include_router(notification_router, prefix=API_PREFIX)

app.include_router(plan_router, prefix=API_PREFIX)
app.include_router(subscription_router, prefix=API_PREFIX)
app.include_router(payment_router, prefix=API_PREFIX)
app.include_router(usage_router, prefix=API_PREFIX)
app.include_router(invoice_router, prefix=API_PREFIX)

app.include_router(refund_router, prefix=API_PREFIX)
app.include_router(coupon_router, prefix=API_PREFIX)
app.include_router(audit_log_router, prefix=API_PREFIX)
app.include_router(competitor_router, prefix=API_PREFIX)
app.include_router(competitor_metric_router, prefix=API_PREFIX)
app.include_router(post_analytic_router, prefix=API_PREFIX)
app.include_router(brand_kit_router, prefix=API_PREFIX)
app.include_router(role_router, prefix=API_PREFIX)
app.include_router(permission_router, prefix=API_PREFIX)
app.include_router(member_role_router, prefix=API_PREFIX)

# =====================================================
# META REQUIRED PAGES
# =====================================================
@app.get("/privacy-policy", response_class=HTMLResponse)
def privacy_policy():
    return """
    <html>
    <head><title>SmartAutoPost Privacy Policy</title></head>
    <body>
    <h1>SmartAutoPost Privacy Policy</h1>
    <p>SmartAutoPost respects user privacy. We only use required social media permissions for publishing and automation services.</p>
    <p>Contact: akashkr915520@gmail.com</p>
    </body>
    </html>
    """

@app.get("/terms", response_class=HTMLResponse)
def terms():
    return """
    <html>
    <head><title>SmartAutoPost Terms</title></head>
    <body>
    <h1>SmartAutoPost Terms of Service</h1>
    <p>By using SmartAutoPost, you agree to our terms and conditions.</p>
    <p>Contact: akashkr915520@gmail.com</p>
    </body>
    </html>
    """

@app.get("/data-deletion", response_class=HTMLResponse)
def data_deletion():
    return """
    <html>
    <head><title>Data Deletion</title></head>
    <body>
    <h1>User Data Deletion Instructions</h1>
    <p>Users can request deletion of their account and associated data from SmartAutoPost.</p>
    <p>To request data deletion please contact: akashkr915520@gmail.com</p>
    </body>
    </html>
    """

# =====================================================
# STATIC + MEDIA MOUNT + WEB FRONTEND
# =====================================================
os.makedirs("uploads/media", exist_ok=True)

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)

app.include_router(web_router)
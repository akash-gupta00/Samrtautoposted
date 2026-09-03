from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    # ============================================================
    # PROJECT
    # ============================================================

    PROJECT_NAME: str = "SmartAutoPost Backend"

    PROJECT_VERSION: str = "1.0.0"

    API_V1_PREFIX: str = "/api/v1"

    PUBLIC_BASE_URL: str = "http://127.0.0.1:8000"

    FRONTEND_URL: str = "https://samrtautoposted.onrender.com"



    # ============================================================
    # DATABASE
    # ============================================================

    DATABASE_URL: str = (
        "postgresql://postgres:Akashpqs@localhost:5432/smartautopost_db"
    )



    # ============================================================
    # JWT
    # ============================================================

    SECRET_KEY: str = "smartautopost-secret-key"

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30



    # ============================================================
    # REFRESH TOKEN
    # ============================================================

    REFRESH_SECRET_KEY: str = (
        "smartautopost-refresh-secret-key"
    )

    REFRESH_TOKEN_EXPIRE_DAYS: int = 7



    # ============================================================
    # CORS
    # ============================================================

    ALLOWED_ORIGINS: list = [

        "http://localhost:3000",

        "http://localhost:5173",

        "http://127.0.0.1:5500",

        "https://smartautopost.com"

    ]



    # ============================================================
    # RATE LIMIT
    # ============================================================

    RATE_LIMIT_PER_MINUTE: int = 100

    RATE_LIMIT_PER_DAY: int = 10000



    # ============================================================
    # EMAIL
    # ============================================================

    SMTP_HOST: str = "smtp.gmail.com"

    SMTP_PORT: int = 587

    SMTP_USER: str = "syntaxerrorcode0@gmail.com"

    SMTP_PASSWORD: str = "ycropgrkeqinkikv"

    SMTP_FROM_EMAIL: str = "syntaxerrorcode0@gmail.com"



    # ============================================================
    # REDIS
    # ============================================================

    REDIS_URL: str = (
        "redis://localhost:6379/0"
    )



    # ============================================================
    # CELERY
    # ============================================================

    CELERY_BROKER_URL: str = (
        "redis://localhost:6379/1"
    )

    CELERY_RESULT_BACKEND: str = (
        "redis://localhost:6379/2"
    )



    # ============================================================
    # AWS S3
    # ============================================================

    AWS_ACCESS_KEY_ID: str = (
        "your-aws-access-key"
    )

    AWS_SECRET_ACCESS_KEY: str = (
        "your-aws-secret-key"
    )

    AWS_REGION: str = "ap-south-1"

    AWS_S3_BUCKET_NAME: str = (
        "smartautopost-media"
    )

    AWS_S3_PUBLIC_URL: str = (
        "https://smartautopost-media.s3.ap-south-1.amazonaws.com"
    )



    # ============================================================
    # SOCIAL LOGIN / OAUTH
    # ============================================================


    # -------------------------
    # Google / Google Business Profile (GMB)
    # -------------------------

    GOOGLE_CLIENT_ID: str = "your-google-client-id"

    GOOGLE_CLIENT_SECRET: str = "your-google-client-secret"

    GOOGLE_REDIRECT_URI: str = (
        "https://samrtautoposted.onrender.com/api/v1/auth/google/callback"
    )



    # -------------------------
    # Facebook / Meta
    # -------------------------

    FACEBOOK_CLIENT_ID: str = (
        "your-facebook-client-id"
    )

    FACEBOOK_CLIENT_SECRET: str = (
        "your-facebook-client-secret"
    )

    FACEBOOK_REDIRECT_URI: str = (
        "https://samrtautoposted.onrender.com/api/v1/auth/facebook/callback"
    )



    # -------------------------
    # LinkedIn
    # -------------------------

    LINKEDIN_CLIENT_ID: str = (
        "your-linkedin-client-id"
    )

    LINKEDIN_CLIENT_SECRET: str = (
        "your-linkedin-client-secret"
    )

    LINKEDIN_REDIRECT_URI: str = (
        "https://samrtautoposted.onrender.com/api/v1/auth/linkedin/callback"
    )



    # -------------------------
    # Instagram
    # -------------------------

    INSTAGRAM_CLIENT_ID: str = (
        "your-instagram-client-id"
    )

    INSTAGRAM_CLIENT_SECRET: str = (
        "your-instagram-client-secret"
    )

    INSTAGRAM_REDIRECT_URI: str = (
        "https://samrtautoposted.onrender.com/api/v1/auth/instagram/callback"
    )



    # -------------------------
    # Threads
    # -------------------------

    THREADS_CLIENT_ID: str = (
        "your-threads-client-id"
    )

    THREADS_CLIENT_SECRET: str = (
        "your-threads-client-secret"
    )

    THREADS_REDIRECT_URI: str = (
        "http://localhost:8000/api/v1/auth/threads/callback"
    )



    # ============================================================
    # AI
    # ============================================================

    OPENAI_API_KEY: str = (
        "your-openai-api-key"
    )

    OPENAI_MODEL: str = (
        "gpt-4-turbo"
    )


    GEMINI_API_KEY: str = (
        "your-gemini-api-key"
    )

    GEMINI_MODEL: str = (
        "gemini-1.5-pro"
    )



    # ============================================================
    # META CALLBACK
    # ============================================================

    META_REDIRECT_URI: str = (
        "https://samrtautoposted.onrender.com/api/v1/auth/facebook/callback"
    )



    # ============================================================
    # PAYMENT
    # ============================================================

    STRIPE_SECRET_KEY: str = (
        "your-stripe-secret-key"
    )

    STRIPE_PUBLISHABLE_KEY: str = (
        "your-stripe-publishable-key"
    )

    STRIPE_WEBHOOK_SECRET: str = (
        "your-stripe-webhook-secret"
    )


    RAZORPAY_KEY_ID: str = (
        "your-razorpay-key-id"
    )

    RAZORPAY_KEY_SECRET: str = (
        "your-razorpay-key-secret"
    )

    RAZORPAY_WEBHOOK_SECRET: str = (
        "your-razorpay-webhook-secret"
    )



    # ============================================================
    # LOGGING
    # ============================================================

    LOG_LEVEL: str = "INFO"

    LOG_FILE: str = "logs/app.log"



    # ============================================================
    # ENVIRONMENT
    # ============================================================

    ENVIRONMENT: str = "development"

    DEBUG: bool = True



    class Config:

        env_file = ".env"

        env_file_encoding = "utf-8"

        case_sensitive = True

        extra = "ignore"



settings = Settings()
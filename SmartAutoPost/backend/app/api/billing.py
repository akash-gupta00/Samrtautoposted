from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user

router = APIRouter(prefix="/api/v1", tags=["Billing"])

# ============================================
# API 10: List Plans
# ============================================
@router.get("/plans")
async def get_plans(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List all subscription plans.
    """
    # TODO: Implement this
    return {
        "success": True,
        "data": {
            "plans": [
                {
                    "id": "free",
                    "name": "Free",
                    "price": 0,
                    "currency": "USD",
                    "max_accounts": 1,
                    "max_posts": 20,
                    "max_clients": 0,
                    "max_team_members": 1,
                    "features": ["Basic Analytics", "1 Social Account"]
                },
                {
                    "id": "pro",
                    "name": "Pro",
                    "price": 49,
                    "currency": "USD",
                    "max_accounts": 10,
                    "max_posts": 9999,
                    "max_clients": 5,
                    "max_team_members": 5,
                    "features": ["Advanced Analytics", "10 Social Accounts", "AI Content"]
                },
                {
                    "id": "agency",
                    "name": "Agency",
                    "price": 199,
                    "currency": "USD",
                    "max_accounts": 50,
                    "max_posts": 9999,
                    "max_clients": 50,
                    "max_team_members": 20,
                    "features": ["Client Management", "Team Collaboration", "White Label"]
                },
                {
                    "id": "enterprise",
                    "name": "Enterprise",
                    "price": 499,
                    "currency": "USD",
                    "max_accounts": 999,
                    "max_posts": 9999,
                    "max_clients": 999,
                    "max_team_members": 999,
                    "features": ["Custom Limits", "Dedicated Support", "Custom Features"]
                }
            ]
        }
    }


# ============================================
# API 11: Create Subscription
# ============================================
@router.post("/subscriptions")
async def create_subscription(
    plan_id: str,
    organization_id: str,
    payment_method: str = "stripe",  # stripe, razorpay
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create a new subscription.
    
    Flow:
    1. Validate plan exists
    2. Check if organization already has subscription
    3. Create payment gateway subscription (Stripe/Razorpay)
    4. Store subscription in database
    5. Return subscription details
    """
    # TODO: Implement this
    return {
        "success": True,
        "data": {
            "subscription_id": "sub_123456",
            "plan_id": plan_id,
            "organization_id": organization_id,
            "status": "active",
            "start_date": "2026-07-13",
            "end_date": "2026-08-13",
            "payment_gateway": payment_method,
            "payment_link": "https://stripe.com/pay/123456"
        }
    }


# ============================================
# API 12: Get Current Subscription
# ============================================
@router.get("/subscriptions/current")
async def get_current_subscription(
    organization_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get current subscription details.
    """
    # TODO: Implement this
    return {
        "success": True,
        "data": {
            "subscription_id": "sub_123456",
            "plan": {
                "id": "pro",
                "name": "Pro",
                "price": 49
            },
            "status": "active",
            "start_date": "2026-06-13",
            "end_date": "2026-07-13",
            "usage": {
                "posts_used": 87,
                "posts_limit": 9999,
                "accounts_used": 4,
                "accounts_limit": 10,
                "clients_used": 2,
                "clients_limit": 5
            },
            "billing_cycle": "monthly",
            "next_billing_date": "2026-08-13"
        }
    }


# ============================================
# API 13: Cancel Subscription
# ============================================
@router.delete("/subscriptions/current")
async def cancel_subscription(
    organization_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Cancel current subscription.
    """
    # TODO: Implement this
    return {
        "success": True,
        "message": "Subscription cancelled successfully",
        "data": {
            "subscription_id": "sub_123456",
            "status": "cancelled",
            "cancelled_at": "2026-07-13T12:00:00Z",
            "active_until": "2026-08-13"
        }
    }


# ============================================
# API 14: Payment History
# ============================================
@router.get("/payments")
async def get_payment_history(
    organization_id: str,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get payment history.
    """
    # TODO: Implement this
    return {
        "success": True,
        "data": {
            "payments": [
                {
                    "id": "pay_123",
                    "amount": 49,
                    "currency": "USD",
                    "status": "paid",
                    "payment_gateway": "stripe",
                    "transaction_id": "txn_123",
                    "date": "2026-07-13T10:00:00Z",
                    "description": "Pro Plan - Monthly"
                },
                {
                    "id": "pay_122",
                    "amount": 49,
                    "currency": "USD",
                    "status": "paid",
                    "payment_gateway": "stripe",
                    "transaction_id": "txn_122",
                    "date": "2026-06-13T10:00:00Z",
                    "description": "Pro Plan - Monthly"
                }
            ],
            "total": 2,
            "total_amount": 98
        }
    }


# ============================================
# API 15: Download Invoice
# ============================================
@router.get("/payments/invoice/{invoice_id}")
async def download_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Download invoice as PDF.
    """
    # TODO: Implement this
    return {
        "success": True,
        "data": {
            "invoice_url": "https://storage.smartautopost.com/invoices/invoice_123.pdf",
            "download_link": "/api/v1/payments/invoice/123/download"
        }
    }
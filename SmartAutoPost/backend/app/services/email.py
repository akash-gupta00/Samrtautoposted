# ============================================================
# EMAIL SERVICE — Send emails using SMTP
# ============================================================

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None
) -> bool:
    """
    Email send karne ka function.
    
    Args:
        to_email: Receiver email
        subject: Email subject
        body: Plain text body
        html_body: HTML body (optional)
    
    Returns:
        True if email sent successfully, False otherwise
    """
    
    # Agar SMTP settings nahi hain toh log karo aur return False
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP settings not configured. Email not sent.")
        return False
    
    try:
        # Email message create karo
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = to_email
        
        # Plain text part
        part1 = MIMEText(body, "plain")
        msg.attach(part1)
        
        # HTML part (agar diya gaya ho)
        if html_body:
            part2 = MIMEText(html_body, "html")
            msg.attach(part2)
        
        # SMTP connection
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())
        
        logger.info(f"Email sent to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False


def send_verification_email(to_email: str, token: str) -> bool:
    """
    Email verification link send karega.
    
    Args:
        to_email: User's email
        token: Verification token
    
    Returns:
        True if sent successfully
    """
    
    # ✅ SAHI URL — No /api/v1 in email link
    verification_url = f"http://localhost:8000/auth/verify-email?token={token}"
    
    subject = "Verify Your Email - SmartAutoPost"
    
    body = f"""
Hello,

Welcome to SmartAutoPost! Please verify your email address by clicking the link below:

{verification_url}

This link will expire in 24 hours.

If you didn't create an account with us, please ignore this email.

Thanks,
Team SmartAutoPost
    """
    
    html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #2563eb;">SmartAutoPost</h2>
    <h3>Verify Your Email</h3>
    <p>Welcome to SmartAutoPost! Please verify your email address by clicking the button below:</p>
    <p style="text-align: center; margin: 30px 0;">
        <a href="{verification_url}" style="background: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; font-weight: bold;">Verify Email</a>
    </p>
    <p style="color: #64748b; font-size: 14px;">This link will expire in 24 hours.</p>
    <hr style="border: 1px solid #e2e8f0; margin: 20px 0;">
    <p style="color: #94a3b8; font-size: 12px;">If you didn't create an account with us, please ignore this email.</p>
</body>
</html>
    """
    
    return send_email(to_email, subject, body, html_body)


def send_password_reset_email(to_email: str, token: str) -> bool:
    """
    Password reset link send karega.
    
    Args:
        to_email: User's email
        token: Password reset token
    
    Returns:
        True if sent successfully
    """
    
    # ✅ FIX: "reset_token" (undefined) ki jagah "token" use kiya —
    # ye hi is function ka actual parameter naam hai
    reset_link = f"http://localhost:8000/api/v1/auth/reset-password?token={token}"
    
    subject = "Reset Your Password - SmartAutoPost"
    
    body = f"""
Hello,

We received a request to reset your password. Click the link below to set a new password:

{reset_link}

This link will expire in 24 hours.

If you didn't request this, please ignore this email.

Thanks,
Team SmartAutoPost
    """
    
    html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #2563eb;">SmartAutoPost</h2>
    <h3>Reset Your Password</h3>
    <p>We received a request to reset your password. Click the button below to set a new password:</p>
    <p style="text-align: center; margin: 30px 0;">
        <a href="{reset_link}" style="background: #ef4444; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; font-weight: bold;">Reset Password</a>
    </p>
    <p style="color: #64748b; font-size: 14px;">This link will expire in 24 hours.</p>
    <hr style="border: 1px solid #e2e8f0; margin: 20px 0;">
    <p style="color: #94a3b8; font-size: 12px;">If you didn't request this, please ignore this email.</p>
</body>
</html>
    """
    
    return send_email(to_email, subject, body, html_body)


def send_welcome_email(to_email: str, name: str) -> bool:
    """
    Welcome email send karega.
    
    Args:
        to_email: User's email
        name: User's name
    
    Returns:
        True if sent successfully
    """
    
    subject = "Welcome to SmartAutoPost!"
    
    body = f"""
Hello {name},

Welcome to SmartAutoPost! We're excited to have you on board.

Here are some things you can do:
1. Connect your social media accounts
2. Generate AI-powered content
3. Schedule and publish posts
4. Track your analytics

If you need any help, feel free to reach out.

Thanks,
Team SmartAutoPost
    """
    
    html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #2563eb;">SmartAutoPost</h2>
    <h3>Welcome, {name}! 🎉</h3>
    <p>We're excited to have you on board. Here are some things you can do:</p>
    <ul>
        <li>🔗 Connect your social media accounts</li>
        <li>🤖 Generate AI-powered content</li>
        <li>📅 Schedule and publish posts</li>
        <li>📊 Track your analytics</li>
    </ul>
    <p>If you need any help, feel free to reach out.</p>
    <hr style="border: 1px solid #e2e8f0; margin: 20px 0;">
    <p style="color: #94a3b8; font-size: 12px;">Team SmartAutoPost</p>
</body>
</html>
    """
    
    return send_email(to_email, subject, body, html_body)


def send_subscription_email(to_email: str, plan_name: str, amount: float) -> bool:
    """
    Subscription confirmation email.
    
    Args:
        to_email: User's email
        plan_name: Plan name (Free, Pro, Agency, Enterprise)
        amount: Amount paid
    
    Returns:
        True if sent successfully
    """
    
    subject = f"Subscription Confirmed - {plan_name} Plan"
    
    body = f"""
Hello,

Your subscription to the {plan_name} plan has been confirmed!

Amount: ${amount}/month

You now have access to all features included in this plan.

Thanks for choosing SmartAutoPost!

Team SmartAutoPost
    """
    
    html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #2563eb;">SmartAutoPost</h2>
    <h3>Subscription Confirmed ✅</h3>
    <p>Your subscription to the <strong>{plan_name}</strong> plan has been confirmed!</p>
    <p style="font-size: 24px; color: #059669; font-weight: bold;">${amount}/month</p>
    <p>You now have access to all features included in this plan.</p>
    <p>Thanks for choosing SmartAutoPost!</p>
    <hr style="border: 1px solid #e2e8f0; margin: 20px 0;">
    <p style="color: #94a3b8; font-size: 12px;">Team SmartAutoPost</p>
</body>
</html>
    """
    
    return send_email(to_email, subject, body, html_body)


def send_notification_email(to_email: str, title: str, message: str) -> bool:
    """
    General notification email.
    
    Args:
        to_email: User's email
        title: Notification title
        message: Notification message
    
    Returns:
        True if sent successfully
    """
    
    subject = f"SmartAutoPost: {title}"
    
    body = f"""
Hello,

{message}

Thanks,
Team SmartAutoPost
    """
    
    html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #2563eb;">SmartAutoPost</h2>
    <h3>{title}</h3>
    <p>{message}</p>
    <hr style="border: 1px solid #e2e8f0; margin: 20px 0;">
    <p style="color: #94a3b8; font-size: 12px;">Team SmartAutoPost</p>
</body>
</html>
    """
    
    return send_email(to_email, subject, body, html_body)
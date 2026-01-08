"""
Email Service.

Handles sending emails for verification, password reset, etc.
Uses SMTP (Gmail or other providers).
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending emails via SMTP.
    """
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_name = settings.EMAIL_FROM_NAME
        self.from_address = settings.EMAIL_FROM_ADDRESS or settings.SMTP_USER
        self.frontend_url = settings.FRONTEND_URL
    
    def _is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return all([
            self.smtp_user,
            self.smtp_password,
            self.from_address,
        ])
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Send an email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML body
            text_content: Plain text body (optional)
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self._is_configured():
            logger.warning("Email service not configured - skipping email send")
            # In development, log the email content
            if settings.ENV == "development":
                logger.info(f"[DEV] Would send email to {to_email}:")
                logger.info(f"[DEV] Subject: {subject}")
                logger.info(f"[DEV] Content preview: {html_content[:200]}...")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_address}>"
            msg["To"] = to_email
            
            # Add text and HTML parts
            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))
            
            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_address, to_email, msg.as_string())
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    async def send_verification_email(
        self,
        to_email: str,
        user_name: Optional[str],
        verification_token: str,
    ) -> bool:
        """
        Send email verification link.
        """
        verification_url = f"{self.frontend_url}/verify-email?token={verification_token}"
        
        name = user_name or "there"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #4F46E5;
                    color: white !important;
                    text-decoration: none;
                    border-radius: 6px;
                    margin: 20px 0;
                }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Welcome to DocLearn! 🎓</h1>
                <p>Hi {name},</p>
                <p>Thanks for signing up! Please verify your email address to get started with personalized AI tutoring.</p>
                <a href="{verification_url}" class="button">Verify Email Address</a>
                <p>Or copy and paste this link in your browser:</p>
                <p style="word-break: break-all; color: #4F46E5;">{verification_url}</p>
                <p>This link will expire in {settings.EMAIL_VERIFICATION_EXPIRY_HOURS} hours.</p>
                <div class="footer">
                    <p>If you didn't create an account, you can safely ignore this email.</p>
                    <p>— The DocLearn Team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Welcome to DocLearn!

Hi {name},

Thanks for signing up! Please verify your email address by clicking the link below:

{verification_url}

This link will expire in {settings.EMAIL_VERIFICATION_EXPIRY_HOURS} hours.

If you didn't create an account, you can safely ignore this email.

— The DocLearn Team
        """
        
        return await self.send_email(
            to_email=to_email,
            subject="Verify your DocLearn email",
            html_content=html_content,
            text_content=text_content,
        )
    
    async def send_password_reset_email(
        self,
        to_email: str,
        user_name: Optional[str],
        reset_token: str,
    ) -> bool:
        """
        Send password reset link.
        """
        reset_url = f"{self.frontend_url}/reset-password?token={reset_token}"
        
        name = user_name or "there"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #4F46E5;
                    color: white !important;
                    text-decoration: none;
                    border-radius: 6px;
                    margin: 20px 0;
                }}
                .warning {{ color: #DC2626; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Reset Your Password 🔐</h1>
                <p>Hi {name},</p>
                <p>We received a request to reset your password. Click the button below to create a new password:</p>
                <a href="{reset_url}" class="button">Reset Password</a>
                <p>Or copy and paste this link in your browser:</p>
                <p style="word-break: break-all; color: #4F46E5;">{reset_url}</p>
                <p class="warning">⚠️ This link will expire in {settings.PASSWORD_RESET_EXPIRY_HOURS} hour(s).</p>
                <div class="footer">
                    <p>If you didn't request a password reset, please ignore this email or contact support if you're concerned.</p>
                    <p>— The DocLearn Team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Reset Your Password

Hi {name},

We received a request to reset your password. Click the link below to create a new password:

{reset_url}

This link will expire in {settings.PASSWORD_RESET_EXPIRY_HOURS} hour(s).

If you didn't request a password reset, please ignore this email.

— The DocLearn Team
        """
        
        return await self.send_email(
            to_email=to_email,
            subject="Reset your DocLearn password",
            html_content=html_content,
            text_content=text_content,
        )
    
    async def send_welcome_email(
        self,
        to_email: str,
        user_name: Optional[str],
    ) -> bool:
        """
        Send welcome email after verification.
        """
        name = user_name or "there"
        dashboard_url = f"{self.frontend_url}/dashboard"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #4F46E5;
                    color: white !important;
                    text-decoration: none;
                    border-radius: 6px;
                    margin: 20px 0;
                }}
                .feature {{ margin: 10px 0; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>You're All Set! 🎉</h1>
                <p>Hi {name},</p>
                <p>Your email has been verified and your DocLearn account is ready!</p>
                
                <h2>What you can do now:</h2>
                <div class="feature">📚 <strong>Create a Learning Plan</strong> - Get a personalized curriculum on any topic</div>
                <div class="feature">🤖 <strong>Learn with AI</strong> - Interactive tutoring that adapts to your pace</div>
                <div class="feature">📈 <strong>Track Progress</strong> - See your learning journey unfold</div>
                
                <a href="{dashboard_url}" class="button">Start Learning</a>
                
                <div class="footer">
                    <p>Happy learning!</p>
                    <p>— The DocLearn Team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(
            to_email=to_email,
            subject="Welcome to DocLearn! 🎓",
            html_content=html_content,
        )


# Singleton instance
email_service = EmailService()

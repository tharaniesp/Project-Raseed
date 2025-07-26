# app/services/notification_service.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.core.database import db
from app.models.notification import (
    NotificationRequest, NotificationResult, NotificationType,
    NotificationPriority, NotificationCategory, NotificationTemplate,
    NotificationPreferences, ScheduledNotification
)

logger = logging.getLogger(__name__)

# Check for email availability
EMAIL_AVAILABLE = True
try:
    import smtplib
except ImportError:
    EMAIL_AVAILABLE = False
    logger.warning("⚠️ SMTP email not available")

# Check for FCM availability
FCM_AVAILABLE = True
try:
    from firebase_admin import messaging
except ImportError:
    FCM_AVAILABLE = False
    logger.warning("⚠️ FCM not available")


class NotificationService:
    """Service for handling notifications via multiple channels"""

    def __init__(self):
        self.db = db
        self.templates = self._load_notification_templates()

        # Initialize FCM
        self.fcm_available = FCM_AVAILABLE

        # Initialize SMTP config
        self.email_available = EMAIL_AVAILABLE
        if EMAIL_AVAILABLE:
            self.smtp_config = {
                'server': getattr(settings, 'SMTP_SERVER', 'smtp.gmail.com'),
                'port': getattr(settings, 'SMTP_PORT', 587),
                'email': getattr(settings, 'SMTP_EMAIL', ''),
                'password': getattr(settings, 'SMTP_PASSWORD', ''),
                'use_tls': getattr(settings, 'SMTP_USE_TLS', True)
            }
            self.email_available = bool(self.smtp_config['email'] and self.smtp_config['password'])

        logger.info(f"✅ Notification service initialized (FCM: {self.fcm_available}, Email: {self.email_available})")

    def _load_notification_templates(self) -> Dict[str, NotificationTemplate]:
        """Load notification templates from database or config"""
        return {}

    async def send_notification(self, request: NotificationRequest) -> NotificationResult:
        notification_id = str(uuid.uuid4())

        try:
            if request.notification_type == NotificationType.EMAIL:
                return await self._send_email_notification(notification_id, request)
            elif request.notification_type == NotificationType.PUSH:
                return await self._send_push_notification(notification_id, request)
            else:
                raise NotImplementedError(f"Notification type {request.notification_type} not implemented")

        except Exception as e:
            logger.error(f"❌ Failed to send notification: {e}")
            return NotificationResult(
                notification_id=notification_id,
                user_id=request.user_id,
                notification_type=request.notification_type,
                status='failed',
                error_message=str(e),
                sent_at=None
            )

    async def _send_push_notification(self, notification_id: str, request: NotificationRequest) -> NotificationResult:
        return NotificationResult(
            notification_id=notification_id,
            user_id=request.user_id,
            notification_type=NotificationType.PUSH,
            status='not_implemented',
            error_message="Push notifications not yet implemented",
            sent_at=None
        )

    async def _get_user_email(self, user_id: str) -> Optional[str]:
        """Stub for user email lookup"""
        return "user@example.com"  # Replace with DB lookup

    def _create_email_template(self, request: NotificationRequest) -> str:
        """Create HTML email template"""
        return f"""
        <html>
        <body>
            <h2>{request.title}</h2>
            <p>{request.body}</p>
            {f'<p><a href="{request.action_url}">Click here</a></p>' if request.action_url else ''}
        </body>
        </html>
        """

    async def _send_email_notification(self, notification_id: str, request: NotificationRequest) -> NotificationResult:
        try:
            if not self.email_available:
                raise Exception("Email service not configured")

            user_email = await self._get_user_email(request.user_id)
            if not user_email:
                raise Exception(f"No email found for user {request.user_id}")

            html_content = self._create_email_template(request)

            success = await self._send_smtp_email(
                to_email=user_email,
                subject=request.title,
                html_body=html_content
            )

            if not success:
                raise Exception("SMTP email sending failed")

            return NotificationResult(
                notification_id=notification_id,
                user_id=request.user_id,
                notification_type=NotificationType.EMAIL,
                status='sent',
                sent_at=datetime.now(),
                tracking_data={'smtp_server': self.smtp_config['server']}
            )

        except Exception as e:
            logger.error(f"❌ Email notification failed: {e}")
            return NotificationResult(
                notification_id=notification_id,
                user_id=request.user_id,
                notification_type=NotificationType.EMAIL,
                status='failed',
                error_message=str(e),
                sent_at=None
            )

    async def _send_smtp_email(self, to_email: str, subject: str, html_body: str) -> bool:
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_config['email']
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(html_body, 'html', 'utf-8'))

            server = smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port'])
            if self.smtp_config['use_tls']:
                server.starttls()
            server.login(self.smtp_config['email'], self.smtp_config['password'])
            server.sendmail(self.smtp_config['email'], to_email, msg.as_string())
            server.quit()

            logger.info(f"✅ Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"❌ SMTP email failed: {e}")
            return False

    # ... [Other methods remain unchanged; you can copy as needed]

    async def test_notification_system(self, user_id: str) -> Dict[str, Any]:
        test_request = NotificationRequest(
            user_id=user_id,
            notification_type=NotificationType.EMAIL,
            priority=NotificationPriority.NORMAL,
            category=NotificationCategory.SYSTEM,
            title="Test Notification",
            body="This is a test notification to verify the system is working."
        )
        result = await self.send_notification(test_request)
        return {
            "test_status": "completed",
            "notification_result": result.dict()
        }


# Singleton instance
notification_service = NotificationService()

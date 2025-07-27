# app/services/notification_service.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import uuid
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect

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


class WebSocketManager:
    """Manages WebSocket connections for real-time notifications"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_users: Dict[WebSocket, str] = {}
        self.connection_timestamps: Dict[WebSocket, float] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a new WebSocket for a user"""
        # Note: websocket.accept() is now called in the route handler
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        self.connection_users[websocket] = user_id
        self.connection_timestamps[websocket] = asyncio.get_event_loop().time()
        
        logger.info(f"🔌 WebSocket connected for user {user_id}")
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket"""
        user_id = self.connection_users.get(websocket)
        if user_id:
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            # Clean up tracking dictionaries
            self.connection_users.pop(websocket, None)
            self.connection_timestamps.pop(websocket, None)
            
            logger.info(f"🔌 WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, message: str, user_id: str):
        """Send message to specific user with improved error handling"""
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message)
                    # Update timestamp on successful send
                    self.connection_timestamps[connection] = asyncio.get_event_loop().time()
                except WebSocketDisconnect:
                    logger.info(f"🔌 WebSocket disconnected during send for user {user_id}")
                    disconnected.add(connection)
                except Exception as e:
                    logger.error(f"❌ Error sending WebSocket message to user {user_id}: {e}")
                    disconnected.add(connection)
            
            # Clean up disconnected connections
            for connection in disconnected:
                self.disconnect(connection)
    
    async def broadcast_to_all(self, message: str):
        """Broadcast message to all connected users with improved error handling"""
        all_connections = set()
        for connections in self.active_connections.values():
            all_connections.update(connections)
        
        disconnected = set()
        for connection in all_connections:
            try:
                await connection.send_text(message)
                # Update timestamp on successful send
                self.connection_timestamps[connection] = asyncio.get_event_loop().time()
            except WebSocketDisconnect:
                disconnected.add(connection)
            except Exception as e:
                logger.error(f"❌ Error broadcasting WebSocket message: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about active connections"""
        total_connections = sum(len(connections) for connections in self.active_connections.values())
        active_users = len(self.active_connections)
        
        # Calculate average connection age
        current_time = asyncio.get_event_loop().time()
        connection_ages = []
        for websocket, timestamp in self.connection_timestamps.items():
            age = current_time - timestamp
            connection_ages.append(age)
        
        avg_age = sum(connection_ages) / len(connection_ages) if connection_ages else 0
        
        return {
            "total_connections": total_connections,
            "active_users": active_users,
            "average_connection_age_seconds": avg_age,
            "oldest_connection_seconds": max(connection_ages) if connection_ages else 0,
            "newest_connection_seconds": min(connection_ages) if connection_ages else 0
        }
    
    def cleanup_stale_connections(self):
        """Clean up connections that haven't been active for too long"""
        current_time = asyncio.get_event_loop().time()
        stale_connections = []
        
        for websocket, timestamp in self.connection_timestamps.items():
            if current_time - timestamp > 3600:  # 1 hour timeout
                stale_connections.append(websocket)
        
        for websocket in stale_connections:
            logger.info(f"🧹 Cleaning up stale WebSocket connection")
            self.disconnect(websocket)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


class NotificationService:
    """Service for handling notifications via multiple channels"""

    def __init__(self):
        self.db = db
        self.templates = self._load_notification_templates()
        self.websocket_manager = websocket_manager

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

        logger.info(f"✅ Notification service initialized (FCM: {self.fcm_available}, Email: {self.email_available}, WebSocket: enabled)")

    def _load_notification_templates(self) -> Dict[str, NotificationTemplate]:
        """Load notification templates from database or config"""
        return {
            "receipt_processed": NotificationTemplate(
                template_id="receipt_processed",
                name="Receipt Processed",
                category=NotificationCategory.RECEIPT_PROCESSED,
                title_template="Receipt Processed",
                body_template="Your receipt has been successfully processed and added to your wallet!",
                supported_types=[NotificationType.PUSH, NotificationType.EMAIL],
                variables=["merchant_name", "receipt_id"],
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            "budget_alert": NotificationTemplate(
                template_id="budget_alert",
                name="Budget Alert",
                category=NotificationCategory.SPENDING_ALERT,
                title_template="Budget Alert",
                body_template="You're approaching your monthly budget limit.",
                supported_types=[NotificationType.PUSH, NotificationType.EMAIL],
                variables=["current_spending", "budget_limit", "percentage"],
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            "spending_insight": NotificationTemplate(
                template_id="spending_insight",
                name="Spending Insight",
                category=NotificationCategory.INSIGHT_AVAILABLE,
                title_template="Spending Insight",
                body_template="New spending pattern detected! Check your insights.",
                supported_types=[NotificationType.PUSH, NotificationType.EMAIL],
                variables=["insight_type", "category", "amount"],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        }

    async def send_notification(self, request: NotificationRequest) -> NotificationResult:
        notification_id = str(uuid.uuid4())

        try:
            # Send via WebSocket first (real-time)
            await self._send_websocket_notification(notification_id, request)
            
            # Send via other channels
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

    async def _send_websocket_notification(self, notification_id: str, request: NotificationRequest):
        """Send real-time notification via WebSocket"""
        try:
            notification_data = {
                "id": notification_id,
                "type": "notification",
                "title": request.title,
                "message": request.body,
                "category": request.category.value if request.category else "general",
                "priority": request.priority.value if request.priority else "normal",
                "timestamp": datetime.now().isoformat(),
                "data": request.data or {}
            }
            
            await self.websocket_manager.send_personal_message(
                json.dumps(notification_data),
                request.user_id
            )
            
            logger.info(f"📡 WebSocket notification sent to user {request.user_id}")
            
        except Exception as e:
            logger.error(f"❌ WebSocket notification failed: {e}")

    async def send_realtime_update(self, user_id: str, update_type: str, data: Dict[str, Any]):
        """Send real-time updates (not notifications)"""
        try:
            update_data = {
                "type": "update",
                "update_type": update_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.websocket_manager.send_personal_message(
                json.dumps(update_data),
                user_id
            )
            
            logger.info(f"📡 Real-time update sent to user {user_id}: {update_type}")
            
        except Exception as e:
            logger.error(f"❌ Real-time update failed: {e}")

    async def send_receipt_processed_notification(self, user_id: str, receipt_id: str, merchant_name: str):
        """Send notification when receipt is processed"""
        request = NotificationRequest(
            user_id=user_id,
            notification_type=NotificationType.PUSH,
            title="Receipt Processed! 📄",
            body=f"Your receipt from {merchant_name} has been processed and added to your wallet.",
            category=NotificationCategory.RECEIPT_PROCESSED,
            priority=NotificationPriority.NORMAL,
            data={"receipt_id": receipt_id, "merchant_name": merchant_name}
        )
        
        return await self.send_notification(request)

    async def send_budget_alert(self, user_id: str, current_spending: float, budget_limit: float):
        """Send budget alert notification"""
        percentage = (current_spending / budget_limit) * 100
        
        if percentage >= 90:
            priority = NotificationPriority.HIGH
            title = "⚠️ Budget Warning!"
        elif percentage >= 75:
            priority = NotificationPriority.NORMAL
            title = "💰 Budget Alert"
        else:
            return  # Don't send notification for low percentages
        
        request = NotificationRequest(
            user_id=user_id,
            notification_type=NotificationType.PUSH,
            title=title,
            body=f"You've spent ${current_spending:.2f} of your ${budget_limit:.2f} budget ({percentage:.1f}%)",
            category=NotificationCategory.SPENDING_ALERT,
            priority=priority,
            data={"current_spending": current_spending, "budget_limit": budget_limit, "percentage": percentage}
        )
        
        return await self.send_notification(request)

    async def send_spending_insight(self, user_id: str, insight_type: str, insight_data: Dict[str, Any]):
        """Send spending insight notification"""
        request = NotificationRequest(
            user_id=user_id,
            notification_type=NotificationType.PUSH,
            title="💡 New Spending Insight",
            body=f"AI detected a new spending pattern: {insight_type}",
            category=NotificationCategory.INSIGHT_AVAILABLE,
            priority=NotificationPriority.NORMAL,
            data={"insight_type": insight_type, "insight_data": insight_data}
        )
        
        return await self.send_notification(request)

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

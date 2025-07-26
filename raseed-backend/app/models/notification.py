# app/models/notification.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    """Types of notifications that can be sent"""
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"

class NotificationPriority(str, Enum):
    """Priority levels for notifications"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class NotificationCategory(str, Enum):
    """Categories of notifications"""
    RECEIPT_PROCESSED = "receipt_processed"
    INSIGHT_AVAILABLE = "insight_available"
    SPENDING_ALERT = "spending_alert"
    REMINDER = "reminder"
    SYSTEM = "system"
    PROMOTIONAL = "promotional"
    SECURITY = "security"

class NotificationRequest(BaseModel):
    """Request model for sending notifications"""
    user_id: str
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    category: NotificationCategory
    title: str
    body: str
    data: Optional[Dict[str, Any]] = None
    action_url: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    template_id: Optional[str] = None

class NotificationResult(BaseModel):
    """Result model for notification sending"""
    notification_id: str
    user_id: str
    notification_type: NotificationType
    status: str  # sent, failed, pending, expired
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    tracking_data: Optional[Dict[str, Any]] = None

class NotificationTemplate(BaseModel):
    """Template for notifications"""
    template_id: str
    name: str
    category: NotificationCategory
    title_template: str
    body_template: str
    supported_types: List[NotificationType]
    variables: List[str] = []
    created_at: datetime
    updated_at: datetime

class NotificationPreferences(BaseModel):
    """User notification preferences"""
    user_id: str
    push_enabled: bool = True
    email_enabled: bool = True
    sms_enabled: bool = False
    categories_enabled: Dict[str, bool] = {}
    quiet_hours_start: Optional[str] = None  # HH:MM format
    quiet_hours_end: Optional[str] = None
    timezone: str = "UTC"
    updated_at: datetime

class ScheduledNotification(BaseModel):
    """Scheduled notification model"""
    notification_id: str
    user_id: str
    notification_request: NotificationRequest
    scheduled_time: datetime
    status: str  # pending, sent, failed, cancelled
    created_at: datetime
    sent_at: Optional[datetime] = None
    attempts: int = 0
    max_attempts: int = 3

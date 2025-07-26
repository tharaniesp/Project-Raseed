from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MessageTransaction(BaseModel):
    id: Optional[str] = None
    user_id: str
    merchant_name: Optional[str] = None
    amount: float
    currency: Optional[str] = "USD"
    transaction_date: datetime
    message_content: str
    message_id: Optional[str] = None
    source: str = Field(default="gmail", description="Source of the message, e.g., gmail")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    raw_data: Optional[dict] = None 
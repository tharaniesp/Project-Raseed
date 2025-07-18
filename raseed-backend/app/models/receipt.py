# app/models/receipt.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ReceiptStatus(str, Enum):
    """Receipt processing status"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    ERROR = "error"

class FileMetadata(BaseModel):
    """File metadata"""
    original_filename: str
    stored_filename: str
    file_size: int
    content_type: str
    upload_date: datetime

class ExtractedItem(BaseModel):
    """Individual receipt item"""
    name: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    category: Optional[str] = None

class ExtractedData(BaseModel):
    """Extracted receipt data from AI"""
    merchant_name: Optional[str] = None
    merchant_address: Optional[str] = None
    receipt_date: Optional[str] = None
    receipt_time: Optional[str] = None
    items: List[ExtractedItem] = []
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = "USD"
    receipt_number: Optional[str] = None
    payment_method: Optional[str] = None
    confidence_score: Optional[float] = None
    raw_text: Optional[str] = None

class ReceiptCreate(BaseModel):
    """Receipt creation model"""
    file_metadata: FileMetadata
    download_url: str

class ReceiptUpdate(BaseModel):
    """Receipt update model"""
    extracted_data: Optional[ExtractedData] = None
    status: Optional[ReceiptStatus] = None
    processing_error: Optional[str] = None

class ReceiptResponse(BaseModel):
    """Receipt response model"""
    id: str
    file_metadata: FileMetadata
    download_url: str
    status: ReceiptStatus
    extracted_data: Optional[ExtractedData] = None
    processing_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ReceiptListResponse(BaseModel):
    """Receipt list response"""
    receipts: List[ReceiptResponse]
    total: int
    limit: int
    offset: int

class UploadResponse(BaseModel):
    """File upload response"""
    success: bool
    receipt_id: str
    download_url: str
    metadata: Dict[str, Any]
    message: Optional[str] = None

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    status_code: int

# Query Models (for future steps)
class QueryRequest(BaseModel):
    """Natural language query request"""
    query: str
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class QueryResponse(BaseModel):
    """Query response model"""
    answer: str
    confidence: float
    sources: List[str] = []
    suggested_actions: List[str] = []
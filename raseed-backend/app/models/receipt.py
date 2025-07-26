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
    user_id: Optional[str] = None
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

# Query Models for local language functionality
class QueryRequest(BaseModel):
    """Natural language query request"""
    query: str
    user_id: Optional[str] = None
    language: Optional[str] = None  # Auto-detected if not provided
    context: Optional[Dict[str, Any]] = None

class QueryType(str, Enum):
    """Types of queries the system can handle"""
    COOKING_SUGGESTIONS = "cooking_suggestions"
    SHOPPING_LIST = "shopping_list"
    INVENTORY_CHECK = "inventory_check"
    SPENDING_ANALYSIS = "spending_analysis"
    GENERAL = "general"

class ActionableItem(BaseModel):
    """Items that can be added to shopping lists or wallet passes"""
    name: str
    quantity: Optional[str] = None
    category: Optional[str] = None
    estimated_price: Optional[float] = None
    priority: Optional[str] = "normal"  # low, normal, high

class QueryResponse(BaseModel):
    """Query response model"""
    answer: str
    confidence: float
    query_type: QueryType
    detected_language: Optional[str] = None
    sources: List[str] = []
    actionable_items: List[ActionableItem] = []
    can_create_wallet_pass: bool = False
    suggested_actions: List[str] = []

class WalletPassRequest(BaseModel):
    """Request to create wallet pass from query response"""
    query_id: str
    pass_title: Optional[str] = None
    custom_items: Optional[List[ActionableItem]] = None

class WalletPassResponse(BaseModel):
    """Wallet pass creation response"""
    success: bool
    wallet_object_id: Optional[str] = None
    save_url: Optional[str] = None
    class_id: Optional[str] = None
    error: Optional[str] = None
    items_count: int = 0

# Enhanced models for shopping list generation
class ShoppingListItem(BaseModel):
    """Shopping list item with enhanced metadata"""
    name: str
    quantity: str
    category: str
    estimated_price: Optional[float] = None
    priority: str = "normal"
    suggested_store: Optional[str] = None
    notes: Optional[str] = None

class ShoppingListResponse(BaseModel):
    """Shopping list generation response"""
    title: str
    items: List[ShoppingListItem]
    total_estimated_cost: Optional[float] = None
    suggested_stores: List[str] = []
    budget_friendly_alternatives: List[str] = []
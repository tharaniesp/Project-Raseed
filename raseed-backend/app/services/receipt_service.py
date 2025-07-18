# app/services/receipt_service.py
from fastapi import UploadFile, HTTPException
from typing import List, Optional
import uuid
from datetime import datetime
import logging

from app.core.database import get_firestore_client, get_storage_bucket, is_firebase_initialized
from app.core.config import settings
from app.models.receipt import (
    ReceiptCreate, ReceiptUpdate, ReceiptResponse, ReceiptStatus,
    FileMetadata, UploadResponse
)

logger = logging.getLogger(__name__)

class ReceiptService:
    """Service class for receipt operations"""
    
    @staticmethod
    def validate_file(file: UploadFile) -> bool:
        """Validate uploaded file"""
        if file.content_type not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(settings.ALLOWED_FILE_TYPES)}"
            )
        
        if file.size and file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size must be less than {settings.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        return True
    
    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        """Generate unique filename"""
        file_extension = original_filename.split('.')[-1] if '.' in original_filename else ''
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"receipts/{timestamp}_{unique_id}.{file_extension}"
    
    @staticmethod
    async def upload_to_storage(file: UploadFile, filename: str) -> str:
        """Upload file to Firebase Storage"""
        if not is_firebase_initialized():
            raise HTTPException(
                status_code=500,
                detail="Firebase not configured"
            )
        
        try:
            bucket = get_storage_bucket()
            if not bucket:
                raise HTTPException(status_code=500, detail="Storage bucket not available")
            
            # Read file content
            file_content = await file.read()
            
            # Upload to storage
            blob = bucket.blob(filename)
            blob.upload_from_string(file_content, content_type=file.content_type)
            blob.make_public()
            
            return blob.public_url
            
        except Exception as e:
            logger.error(f"Storage upload error: {e}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
    @staticmethod
    async def create_receipt(receipt_data: ReceiptCreate) -> str:
        """Create receipt record in Firestore"""
        if not is_firebase_initialized():
            # Demo mode
            return f"demo_{uuid.uuid4().hex[:8]}"
        
        try:
            db = get_firestore_client()
            if not db:
                raise HTTPException(status_code=500, detail="Database not available")
            
            # Prepare document data
            doc_data = {
                "file_metadata": receipt_data.file_metadata.dict(),
                "download_url": receipt_data.download_url,
                "status": ReceiptStatus.UPLOADED.value,
                "extracted_data": None,
                "processing_error": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Save to Firestore
            doc_ref = db.collection(settings.FIRESTORE_COLLECTION_RECEIPTS).add(doc_data)
            receipt_id = doc_ref[1].id
            
            logger.info(f"Receipt created with ID: {receipt_id}")
            return receipt_id
            
        except Exception as e:
            logger.error(f"Firestore save error: {e}")
            raise HTTPException(status_code=500, detail=f"Database save failed: {str(e)}")
    
    @staticmethod
    async def upload_receipt(file: UploadFile) -> UploadResponse:
        """Main upload receipt method"""
        try:
            # Validate file
            ReceiptService.validate_file(file)
            
            # Generate unique filename
            unique_filename = ReceiptService.generate_unique_filename(file.filename)
            
            if is_firebase_initialized():
                # Upload to Firebase Storage
                download_url = await ReceiptService.upload_to_storage(file, unique_filename)
                
                # Create file metadata
                file_metadata = FileMetadata(
                    original_filename=file.filename,
                    stored_filename=unique_filename,
                    file_size=file.size,
                    content_type=file.content_type,
                    upload_date=datetime.utcnow()
                )
                
                # Create receipt record
                receipt_create = ReceiptCreate(
                    file_metadata=file_metadata,
                    download_url=download_url
                )
                
                receipt_id = await ReceiptService.create_receipt(receipt_create)
                
                return UploadResponse(
                    success=True,
                    receipt_id=receipt_id,
                    download_url=download_url,
                    metadata={
                        "filename": file.filename,
                        "size": file.size,
                        "type": file.content_type
                    }
                )
            else:
                # Demo mode
                mock_receipt_id = f"demo_{uuid.uuid4().hex[:8]}"
                return UploadResponse(
                    success=True,
                    receipt_id=mock_receipt_id,
                    download_url=f"https://demo.storage.com/{unique_filename}",
                    metadata={
                        "filename": file.filename,
                        "size": file.size,
                        "type": file.content_type
                    },
                    message="Demo mode - Firebase not configured"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Upload error: {e}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
    @staticmethod
    async def get_receipts(limit: int = 10, offset: int = 0) -> List[ReceiptResponse]:
        """Get list of receipts"""
        if not is_firebase_initialized():
            return []
        
        try:
            db = get_firestore_client()
            if not db:
                return []
            
            # Query Firestore
            query = (db.collection(settings.FIRESTORE_COLLECTION_RECEIPTS)
                    .order_by('created_at', direction='DESCENDING')
                    .limit(limit)
                    .offset(offset))
            
            docs = query.stream()
            receipts = []
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                
                # Convert timestamps
                if 'created_at' in data and data['created_at']:
                    data['created_at'] = data['created_at'].replace(tzinfo=None)
                if 'updated_at' in data and data['updated_at']:
                    data['updated_at'] = data['updated_at'].replace(tzinfo=None)
                
                receipt = ReceiptResponse(**data)
                receipts.append(receipt)
            
            return receipts
            
        except Exception as e:
            logger.error(f"Get receipts error: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch receipts: {str(e)}")
    
    @staticmethod
    async def get_receipt_by_id(receipt_id: str) -> Optional[ReceiptResponse]:
        """Get receipt by ID"""
        if not is_firebase_initialized():
            return None
        
        try:
            db = get_firestore_client()
            if not db:
                return None
            
            doc_ref = db.collection(settings.FIRESTORE_COLLECTION_RECEIPTS).document(receipt_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            data['id'] = doc.id
            
            # Convert timestamps
            if 'created_at' in data and data['created_at']:
                data['created_at'] = data['created_at'].replace(tzinfo=None)
            if 'updated_at' in data and data['updated_at']:
                data['updated_at'] = data['updated_at'].replace(tzinfo=None)
            
            return ReceiptResponse(**data)
            
        except Exception as e:
            logger.error(f"Get receipt error: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch receipt: {str(e)}")
    
    @staticmethod
    async def update_receipt(receipt_id: str, update_data: ReceiptUpdate) -> bool:
        """Update receipt"""
        if not is_firebase_initialized():
            return False
        
        try:
            db = get_firestore_client()
            if not db:
                return False
            
            # Prepare update data
            update_dict = {"updated_at": datetime.utcnow()}
            
            if update_data.extracted_data:
                update_dict["extracted_data"] = update_data.extracted_data.dict()
            
            if update_data.status:
                update_dict["status"] = update_data.status.value
            
            if update_data.processing_error:
                update_dict["processing_error"] = update_data.processing_error
            
            # Update document
            doc_ref = db.collection(settings.FIRESTORE_COLLECTION_RECEIPTS).document(receipt_id)
            doc_ref.update(update_dict)
            
            logger.info(f"Receipt {receipt_id} updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Update receipt error: {e}")
            return False
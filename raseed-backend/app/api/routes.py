# app/api/routes.py
from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from typing import List

from app.services.receipt_service import ReceiptService
from app.models.receipt import ReceiptListResponse, ReceiptResponse, UploadResponse
from app.core.database import is_firebase_initialized

# Health Router
health_router = APIRouter()

@health_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "firebase_initialized": is_firebase_initialized(),
        "timestamp": "2025-07-18T10:30:00Z"
    }

# Receipt Router
receipt_router = APIRouter()

@receipt_router.post("/upload-receipt", response_model=UploadResponse)
async def upload_receipt(file: UploadFile = File(...)):
    """
    Upload receipt image/video to Firebase Storage and save metadata
    
    Returns:
        - receipt_id: Unique identifier for the receipt
        - download_url: URL to access the uploaded file
        - metadata: File information
    """
    return await ReceiptService.upload_receipt(file)

@receipt_router.get("/receipts", response_model=ReceiptListResponse)
async def get_receipts(
    limit: int = Query(10, ge=1, le=100, description="Number of receipts to return"),
    offset: int = Query(0, ge=0, description="Number of receipts to skip")
):
    """Get list of uploaded receipts"""
    receipts = await ReceiptService.get_receipts(limit=limit, offset=offset)
    
    return ReceiptListResponse(
        receipts=receipts,
        total=len(receipts),
        limit=limit,
        offset=offset
    )

@receipt_router.get("/receipts/{receipt_id}", response_model=ReceiptResponse)
async def get_receipt(receipt_id: str):
    """Get specific receipt by ID"""
    receipt = await ReceiptService.get_receipt_by_id(receipt_id)
    
    if not receipt:
        raise HTTPException(
            status_code=404,
            detail="Receipt not found"
        )
    
    return receipt

# Step 2: AI Processing Routes
@receipt_router.post("/receipts/{receipt_id}/process")
async def process_receipt(receipt_id: str):
    """Process receipt with Gemini Vision AI to extract structured data"""
    from app.services.ai_service import ai_service
    from app.models.receipt import ReceiptUpdate, ReceiptStatus
    
    # Get receipt details
    receipt = await ReceiptService.get_receipt_by_id(receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    # Check if AI service is available
    if not ai_service.is_available():
        raise HTTPException(
            status_code=503, 
            detail="AI service not available. Please check GEMINI_API_KEY configuration."
        )
    
    # Update status to processing
    update_data = ReceiptUpdate(status=ReceiptStatus.PROCESSING)
    await ReceiptService.update_receipt(receipt_id, update_data)
    
    try:
        # Extract data using Gemini Vision
        extracted_data = await ai_service.extract_receipt_data(receipt.download_url)
        
        if extracted_data:
            # Update receipt with extracted data
            update_data = ReceiptUpdate(
                extracted_data=extracted_data,
                status=ReceiptStatus.PROCESSED
            )
            success = await ReceiptService.update_receipt(receipt_id, update_data)
            
            if success:
                return {
                    "success": True,
                    "message": "Receipt processed successfully",
                    "receipt_id": receipt_id,
                    "extracted_data": extracted_data.dict(),
                    "confidence_score": extracted_data.confidence_score
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to save extracted data")
        else:
            # Processing failed
            update_data = ReceiptUpdate(
                status=ReceiptStatus.ERROR,
                processing_error="AI extraction failed - could not extract data from image"
            )
            await ReceiptService.update_receipt(receipt_id, update_data)
            
            raise HTTPException(
                status_code=422, 
                detail="Failed to extract data from receipt image. Please ensure the image is clear and contains a valid receipt."
            )
            
    except Exception as e:
        # Update status to error
        update_data = ReceiptUpdate(
            status=ReceiptStatus.ERROR,
            processing_error=str(e)
        )
        await ReceiptService.update_receipt(receipt_id, update_data)
        
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@receipt_router.get("/receipts/{receipt_id}/processing-status")
async def get_processing_status(receipt_id: str):
    """Get current processing status of a receipt"""
    receipt = await ReceiptService.get_receipt_by_id(receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    return {
        "receipt_id": receipt_id,
        "status": receipt.status,
        "has_extracted_data": receipt.extracted_data is not None,
        "processing_error": receipt.processing_error,
        "confidence_score": receipt.extracted_data.confidence_score if receipt.extracted_data else None,
        "updated_at": receipt.updated_at
    }

@receipt_router.post("/receipts/{receipt_id}/generate-wallet-pass")
async def generate_wallet_pass(receipt_id: str):
    """Generate Google Wallet pass (Step 3)"""
    # TODO: Implement in Step 3
    return {
        "message": "Wallet pass generation will be implemented in Step 3",
        "receipt_id": receipt_id,
        "status": "pending"
    }

@receipt_router.post("/query")
async def query_receipts(query: str):
    """Natural language query (Step 4)"""
    # TODO: Implement in Step 4
    return {
        "message": "Natural language queries will be implemented in Step 4",
        "query": query,
        "answer": "Feature coming soon!"
    }
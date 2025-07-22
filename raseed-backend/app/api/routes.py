# app/api/routes.py - Updated with Auto Wallet Pass Generation
from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from typing import List
import logging

from app.services.receipt_service import ReceiptService
from app.models.receipt import ReceiptListResponse, ReceiptResponse, UploadResponse
from app.core.database import is_firebase_initialized
from app.core.config import settings

logger = logging.getLogger(__name__)

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

# Step 2 + 3: AI Processing with Auto Wallet Pass Generation
@receipt_router.post("/receipts/{receipt_id}/process")
async def process_receipt(receipt_id: str):
    """Process receipt with Gemini Vision AI and auto-generate wallet pass"""
    from app.services.ai_service import ai_service
    from app.services.wallet_service import WalletService
    from app.models.receipt import ReceiptUpdate, ReceiptStatus
    
    logger.info(f"🚀 Starting processing for receipt: {receipt_id}")
    
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
        # STEP 2: Extract data using Gemini Vision
        logger.info(f"🤖 Starting AI extraction for receipt: {receipt_id}")
        extracted_data = await ai_service.extract_receipt_data(receipt.download_url)
        
        if extracted_data:
            # Update receipt with extracted data first
            update_data = ReceiptUpdate(
                extracted_data=extracted_data,
                status=ReceiptStatus.PROCESSED
            )
            success = await ReceiptService.update_receipt(receipt_id, update_data)
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to save extracted data")
            
            logger.info(f"✅ AI extraction successful for receipt: {receipt_id}")
            
            # STEP 3: Auto-generate Wallet Pass (NEW!)
            wallet_pass_data = None
            wallet_error = None
            
            # Check if auto-generation is enabled
            auto_generate = getattr(settings, 'AUTO_GENERATE_WALLET_PASS', True)
            
            if auto_generate:
                try:
                    if WalletService.is_wallet_available():
                        logger.info(f"🎫 Auto-generating wallet pass for receipt: {receipt_id}")
                        wallet_result = await WalletService.generate_pass_for_receipt(receipt_id)
                        
                        wallet_pass_data = {
                            "wallet_object_id": wallet_result["object_id"],
                            "save_url": wallet_result["save_url"],
                            "class_id": wallet_result.get("class_id"),
                            "wallet_state": wallet_result.get("wallet_state", "ACTIVE"),
                            "auto_generated": True,
                            "generation_timestamp": "2025-07-22T10:30:00Z"
                        }
                        logger.info(f"✅ Wallet pass auto-generated: {wallet_result['object_id']}")
                    else:
                        logger.warning("⚠️ Wallet service not available - skipping auto-generation")
                        wallet_error = "Wallet service not configured"
                        
                except Exception as wallet_ex:
                    logger.error(f"❌ Auto wallet pass generation failed: {wallet_ex}")
                    wallet_error = str(wallet_ex)
                    # Don't fail the entire process if wallet generation fails
            else:
                logger.info("ℹ️ Auto wallet pass generation disabled in settings")
                wallet_error = "Auto-generation disabled"
            
            # Prepare comprehensive response
            response_data = {
                "success": True,
                "message": "Receipt processed successfully",
                "receipt_id": receipt_id,
                "extracted_data": extracted_data.dict(),
                "confidence_score": extracted_data.confidence_score,
                "processing_completed_at": "2025-07-22T10:30:00Z"
            }
            
            # Add wallet pass info
            if wallet_pass_data:
                response_data["wallet_pass"] = wallet_pass_data
                response_data["message"] += " and wallet pass created automatically"
                logger.info(f"🎉 Complete processing successful for receipt: {receipt_id}")
            elif wallet_error:
                response_data["wallet_pass"] = {
                    "auto_generated": False,
                    "error": wallet_error,
                    "manual_creation_available": True,
                    "manual_endpoint": f"/api/receipts/{receipt_id}/generate-wallet-pass"
                }
                response_data["message"] += " (wallet pass can be created manually)"
                logger.info(f"⚠️ Processing successful but wallet auto-generation failed: {wallet_error}")
            
            return response_data
            
        else:
            # AI Processing failed
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
        logger.error(f"❌ Processing failed for receipt {receipt_id}: {str(e)}")
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

# Manual Wallet Pass Generation (Fallback)
@receipt_router.post("/receipts/{receipt_id}/generate-wallet-pass")
async def generate_wallet_pass(receipt_id: str):
    """Manually generate Google Wallet pass (fallback if auto-generation failed)"""
    from app.services.wallet_service import WalletService

    logger.info(f"🎫 Manual wallet pass generation requested for receipt: {receipt_id}")

    try:
        # Check if wallet service is available
        if not WalletService.is_wallet_available():
            return {
                "success": False,
                "error": "Google Wallet API not configured. Check service account and project ID."
            }

        result = await WalletService.generate_pass_for_receipt(receipt_id)
        
        logger.info(f"✅ Manual wallet pass generated: {result['object_id']}")
        
        return {
            "success": True,
            "receipt_id": receipt_id,
            "wallet_object_id": result["object_id"],
            "save_url": result["save_url"],
            "class_id": result.get("class_id"),
            "wallet_state": result.get("wallet_state"),
            "auto_generated": False,
            "generation_type": "manual"
        }
    except Exception as e:
        logger.error(f"❌ Manual wallet pass generation failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "receipt_id": receipt_id
        }
    
@receipt_router.get("/receipts/{receipt_id}/wallet-status")
async def get_wallet_status(receipt_id: str):
    """Get Google Wallet pass status"""
    from app.services.wallet_service import WalletService
    
    try:
        result = await WalletService.get_pass_status_by_receipt(receipt_id)
        return result
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Test endpoint for wallet service
@receipt_router.get("/wallet/test")
async def test_wallet_service():
    """Test Google Wallet service configuration"""
    try:
        from app.services.wallet_service import WalletService
        import os
        
        # Check availability
        is_available = WalletService.is_wallet_available()
        
        checks = {
            "service_account_file_exists": os.path.exists(settings.FIREBASE_SERVICE_ACCOUNT_PATH),
            "project_id_set": bool(settings.FIREBASE_PROJECT_ID),
            "issuer_id_set": bool(getattr(settings, 'GOOGLE_WALLET_ISSUER_ID', '')),
            "firebase_initialized": is_firebase_initialized(),
            "auto_generation_enabled": getattr(settings, 'AUTO_GENERATE_WALLET_PASS', True)
        }
        
        if not is_available:
            return {
                "wallet_available": False,
                "error": "Wallet service not configured",
                "checks": checks,
                "recommendations": [
                    "Ensure Firebase service account file exists",
                    "Set FIREBASE_PROJECT_ID in environment",
                    "Set GOOGLE_WALLET_ISSUER_ID (project number recommended)",
                    "Enable Google Wallet API in Google Cloud Console"
                ]
            }
        
        # Try to initialize client
        try:
            client = WalletService.get_wallet_client()
            issuer_id = WalletService.get_issuer_id()
            
            return {
                "wallet_available": True,
                "client_initialized": True,
                "project_id": settings.FIREBASE_PROJECT_ID,
                "issuer_id": issuer_id,
                "checks": checks,
                "message": "Google Wallet service ready!",
                "test_class_id": f"{issuer_id}.raseed_receipt_class"
            }
        except Exception as client_error:
            return {
                "wallet_available": True,
                "client_initialized": False,
                "error": str(client_error),
                "checks": checks,
                "message": "Wallet service configuration issue"
            }
            
    except Exception as e:
        return {
            "wallet_available": False,
            "error": str(e),
            "message": "Failed to test wallet service"
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
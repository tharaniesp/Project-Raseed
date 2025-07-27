# app/api/routes.py - Updated with Auto Wallet Pass Generation and Natural Language Queries
from fastapi import APIRouter, File, UploadFile, HTTPException, Query, WebSocket, WebSocketDisconnect
from typing import List
import logging
import json
import asyncio

from app.services.receipt_service import ReceiptService
from app.services.notification_service import websocket_manager
from app.services.agent_orchestration_service import agent_orchestration_service
from app.services.document_ai_service import document_ai_service
from app.models.receipt import (
    ReceiptListResponse, ReceiptResponse, UploadResponse,
    QueryRequest, QueryResponse, WalletPassRequest, WalletPassResponse,
    ShoppingListResponse
)
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

# WebSocket Router for Real-time Notifications
websocket_router = APIRouter()

@websocket_router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time notifications with improved connection handling"""
    
    # Accept the connection first
    await websocket.accept()
    
    # Connect to manager
    await websocket_manager.connect(websocket, user_id)
    
    try:
        # Send welcome message
        welcome_message = {
            "type": "connection",
            "message": "Connected to Raseed real-time notifications",
            "user_id": user_id,
            "timestamp": "2025-07-26T10:30:00Z"
        }
        await websocket.send_text(json.dumps(welcome_message))
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for any message from client (ping/pong for keep-alive)
                # Add timeout to prevent hanging
                data = await asyncio.wait_for(websocket.receive_text(), timeout=300.0)  # 5 minute timeout
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong", 
                        "timestamp": "2025-07-26T10:30:00Z"
                    }))
                elif message.get("type") == "subscribe":
                    # Handle subscription to specific notification types
                    await websocket.send_text(json.dumps({
                        "type": "subscribed",
                        "channels": message.get("channels", []),
                        "timestamp": "2025-07-26T10:30:00Z"
                    }))
                elif message.get("type") == "heartbeat":
                    # Respond to heartbeat to keep connection alive
                    await websocket.send_text(json.dumps({
                        "type": "heartbeat_ack",
                        "timestamp": "2025-07-26T10:30:00Z"
                    }))
                    
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.send_text(json.dumps({
                        "type": "ping",
                        "timestamp": "2025-07-26T10:30:00Z"
                    }))
                except Exception:
                    # Connection lost, break the loop
                    break
            except WebSocketDisconnect:
                logger.info(f"🔌 WebSocket disconnected normally for user {user_id}")
                break
            except json.JSONDecodeError:
                # Send error for invalid JSON
                try:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format",
                        "timestamp": "2025-07-26T10:30:00Z"
                    }))
                except Exception:
                    # Connection lost, break the loop
                    break
            except Exception as e:
                logger.error(f"❌ WebSocket error for user {user_id}: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket error for user {user_id}: {e}")
    finally:
        websocket_manager.disconnect(websocket)

@websocket_router.get("/ws/status/{user_id}")
async def websocket_status(user_id: str):
    """Check if user has active WebSocket connections"""
    active_connections = websocket_manager.active_connections.get(user_id, set())
    return {
        "user_id": user_id,
        "connected": len(active_connections) > 0,
        "connection_count": len(active_connections),
        "timestamp": "2025-07-26T10:30:00Z"
    }

@websocket_router.get("/notifications/status")
async def notification_system_status():
    """Check the overall status of the notification system"""
    total_connections = sum(len(connections) for connections in websocket_manager.active_connections.values())
    
    return {
        "status": "healthy",
        "total_connections": total_connections,
        "active_users": len(websocket_manager.active_connections),
        "websocket_enabled": True,
        "fcm_enabled": True,
        "email_enabled": False,
        "timestamp": "2025-07-26T10:30:00Z"
    }

@websocket_router.post("/notifications/test/{user_id}")
async def test_notification(user_id: str, notification_type: str = "receipt"):
    """Test notification for a specific user"""
    from app.services.notification_service import NotificationService
    
    notification_service = NotificationService()
    
    try:
        if notification_type == "receipt":
            await notification_service.send_receipt_processed_notification(
                user_id=user_id,
                receipt_id="test_receipt_001",
                merchant_name="Test Store"
            )
            message = "Receipt processed notification sent"
        elif notification_type == "budget":
            await notification_service.send_budget_alert(
                user_id=user_id,
                current_spending=950.00,
                budget_limit=1000.00
            )
            message = "Budget alert notification sent"
        elif notification_type == "insight":
            await notification_service.send_spending_insight(
                user_id=user_id,
                insight_type="Test spending insight",
                insight_data={"category": "test", "amount": 100.00}
            )
            message = "Spending insight notification sent"
        else:
            raise HTTPException(status_code=400, detail="Invalid notification type")
        
        return {
            "success": True,
            "message": message,
            "user_id": user_id,
            "notification_type": notification_type,
            "timestamp": "2025-07-26T10:30:00Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")

@websocket_router.get("/notifications/conditions")
async def get_notification_conditions():
    """Get information about all notification conditions"""
    return {
        "notification_conditions": [
            {
                "type": "receipt_processed",
                "trigger": "When a receipt is successfully processed with AI",
                "priority": "normal",
                "category": "receipt",
                "description": "Notifies user when receipt is processed and wallet pass is created"
            },
            {
                "type": "budget_alert",
                "trigger": "When spending reaches 75% or 90% of budget limit",
                "priority": "medium (75%) or high (90%+)",
                "category": "budget",
                "description": "Alerts user about budget limits and spending thresholds"
            },
            {
                "type": "spending_insight",
                "trigger": "When AI detects spending patterns or anomalies",
                "priority": "normal",
                "category": "insight",
                "description": "Provides AI-generated insights about spending behavior"
            },
            {
                "type": "real_time_update",
                "trigger": "When system updates occur",
                "priority": "normal",
                "category": "update",
                "description": "Real-time updates about system status and processing"
            }
        ],
        "how_to_check": [
            "1. Open frontend at http://localhost:3000",
            "2. Look for bell icon in header",
            "3. Click bell to open notification panel",
            "4. Check badge number for unread count",
            "5. Look for connection status indicator"
        ],
        "how_to_trigger": [
            "1. Upload receipt image (triggers receipt processing)",
            "2. Run test script: python test_notification_conditions.py",
            "3. Use demo script: python test_realtime_demo.py",
            "4. Call API: POST /api/notifications/test/{user_id}"
        ]
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

@receipt_router.options("/upload-receipt")
async def options_upload_receipt():
    """Handle OPTIONS request for upload endpoint"""
    return {"message": "OK"}

@receipt_router.get("/receipts", response_model=ReceiptListResponse)
async def get_receipts(
    limit: int = Query(20, ge=1, le=100, description="Number of receipts to return"),
    offset: int = Query(0, ge=0, description="Number of receipts to skip")
):
    """Get list of uploaded receipts"""
    try:
        receipts = await ReceiptService.get_receipts(limit=limit, offset=offset)
        
        return ReceiptListResponse(
            receipts=receipts,
            total=len(receipts),
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"Error getting receipts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get receipts: {str(e)}")

@receipt_router.options("/receipts")
async def options_receipts():
    """Handle OPTIONS request for receipts endpoint"""
    return {"message": "OK"}

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
                
                # Send real-time notification
                try:
                    from app.services.notification_service import NotificationService
                    notification_service = NotificationService()
                    
                    # Get merchant name from extracted data
                    merchant_name = extracted_data.merchant_name or "Unknown Merchant"
                    
                    # Send notification to user (assuming user_id is available)
                    user_id = "demo_user"  # In real app, get from auth context
                    await notification_service.send_receipt_processed_notification(
                        user_id=user_id,
                        receipt_id=receipt_id,
                        merchant_name=merchant_name
                    )
                    
                    # Send real-time update
                    await notification_service.send_realtime_update(
                        user_id=user_id,
                        update_type="receipt_processed",
                        data={
                            "receipt_id": receipt_id,
                            "merchant_name": merchant_name,
                            "wallet_pass_id": wallet_pass_data["wallet_object_id"],
                            "total_amount": extracted_data.total_amount,
                            "items_count": len(extracted_data.items) if extracted_data.items else 0
                        }
                    )
                    
                    logger.info(f"📡 Real-time notifications sent for receipt: {receipt_id}")
                    
                except Exception as notif_error:
                    logger.error(f"❌ Notification sending failed: {notif_error}")
                    # Don't fail the main process if notifications fail
                    
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

# Natural Language Query Endpoints
@receipt_router.post("/query", response_model=QueryResponse)
async def process_natural_language_query(request: QueryRequest):
    """
    Process natural language queries about receipts and purchases
    
    Examples:
    - "What can I cook with the food I bought from the last two weeks?"
    - "What ingredients do I need to buy to be able to cook this dish?"
    - "Do I have enough laundry detergent for my weekly laundry?"
    """
    from app.services.query_service import query_service
    from app.models.receipt import QueryRequest, QueryResponse
    
    logger.info(f"🔍 Received natural language query: {request.query[:100]}...")
    
    try:
        response = await query_service.process_natural_language_query(request)
        logger.info(f"✅ Query processed successfully. Type: {response.query_type}")
        return response
    except Exception as e:
        logger.error(f"❌ Query processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )

@receipt_router.post("/query/create-wallet-pass", response_model=WalletPassResponse)
async def create_wallet_pass_from_query(request: WalletPassRequest):
    """
    Create a Google Wallet pass from a previous query that generated actionable items
    """
    from app.services.query_service import query_service
    from app.models.receipt import WalletPassRequest, WalletPassResponse
    
    logger.info(f"🎫 Creating wallet pass for query: {request.query_id}")
    
    try:
        response = await query_service.create_wallet_pass_from_query(request)
        
        if response.success:
            logger.info(f"✅ Wallet pass created: {response.wallet_object_id}")
        else:
            logger.warning(f"⚠️ Wallet pass creation failed: {response.error}")
        
        return response
    except Exception as e:
        logger.error(f"❌ Wallet pass creation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create wallet pass: {str(e)}"
        )

@receipt_router.post("/query/shopping-list", response_model=ShoppingListResponse)
async def generate_shopping_list(request: dict):
    """
    Generate a detailed shopping list based on a natural language query
    """
    from app.services.query_service import query_service
    from app.models.receipt import ShoppingListResponse
    
    query = request.get("query", "")
    user_id = request.get("user_id")
    
    logger.info(f"🛒 Generating shopping list for: {query[:50]}...")
    
    try:
        response = await query_service.generate_shopping_list(query, user_id)
        logger.info(f"✅ Shopping list generated with {len(response.items)} items")
        return response
    except Exception as e:
        logger.error(f"❌ Shopping list generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate shopping list: {str(e)}"
        )

@receipt_router.get("/query/statistics")
async def get_query_statistics():
    """Get statistics about recent queries and wallet pass generation"""
    try:
        from app.services.query_service import query_service
        
        # Safely check vertex AI availability
        vertex_ai_available = False
        try:
            from app.services.vertex_ai_agent_service import vertex_ai_agent_service
            vertex_ai_available = vertex_ai_agent_service is not None and vertex_ai_agent_service.is_available()
        except Exception as e:
            logger.warning(f"⚠️ Could not check Vertex AI availability: {e}")
        
        # Safely check wallet service availability
        wallet_service_available = False
        try:
            from app.services.wallet_service import WalletService
            wallet_service_available = WalletService.is_wallet_available()
        except Exception as e:
            logger.warning(f"⚠️ Could not check Wallet service availability: {e}")
        
        stats = query_service.get_query_statistics()
        return {
            "success": True,
            "statistics": stats,
            "vertex_ai_available": vertex_ai_available,
            "wallet_service_available": wallet_service_available
        }
    except Exception as e:
        logger.error(f"❌ Failed to get query statistics: {e}")
        return {
            "success": False,
            "error": str(e),
            "vertex_ai_available": False,
            "wallet_service_available": False
        }

@receipt_router.get("/vertex-ai/status")
async def get_vertex_ai_status():
    """Get Vertex AI configuration and status (simplified - no Data Store needed)"""
    try:
        from app.services.vertex_ai_agent_service import vertex_ai_agent_service
        
        # Check service availability
        agent_available = vertex_ai_agent_service is not None and vertex_ai_agent_service.is_available()
        
        # Get configuration details
        config = {
            "project_id": getattr(settings, 'FIREBASE_PROJECT_ID', None),
            "location": getattr(settings, 'VERTEX_AI_LOCATION', 'us-central1'),
            "model": getattr(settings, 'VERTEX_AI_MODEL', 'gemini-1.5-pro'),
            "multi_language_enabled": getattr(settings, 'ENABLE_MULTI_LANGUAGE', True)
        }
        
        # Check package availability
        packages_status = {}
        required_packages = [
            ('google.cloud.aiplatform', 'Vertex AI Platform'),
            ('vertexai', 'Vertex AI SDK'),
            ('langdetect', 'Language Detection'),
            ('googletrans', 'Google Translate')
        ]
        
        for package, name in required_packages:
            try:
                __import__(package.replace('.', '_') if '.' in package else package)
                packages_status[name] = True
            except ImportError:
                packages_status[name] = False
        
        # Overall status
        fully_configured = (
            agent_available and 
            all(packages_status.values()) and
            config['project_id']
        )
        
        # Get recent receipts count for context
        try:
            receipts = await ReceiptService.get_receipts(limit=100, offset=0)
            processed_receipts = len([r for r in receipts if r.extracted_data])
        except:
            processed_receipts = 0
        
        return {
            "success": True,
            "vertex_ai_status": {
                "service_available": agent_available,
                "fully_configured": fully_configured,
                "using_vertex_ai": agent_available,  # vs Gemini fallback
                "data_source": "Firestore (direct access)",
                "available_receipts": processed_receipts,
                "configuration": config,
                "packages": packages_status
            },
            "recommendations": [] if fully_configured else [
                "Install missing packages: pip install google-cloud-aiplatform vertexai" if not all(packages_status.values()) else None,
                "Enable Vertex AI API in Google Cloud Console" if config['project_id'] and not agent_available else None,
                "Restart server after configuration changes" if config['project_id'] else None
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Vertex AI status check failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "vertex_ai_status": {
                "service_available": False,
                "fully_configured": False,
                "using_vertex_ai": False
            }
        }

@receipt_router.get("/agents/status")
async def get_agent_orchestration_status():
    """Get agent orchestration service status"""
    try:
        status = await agent_orchestration_service.get_agent_status()
        return {
            "agent_orchestration": status,
            "timestamp": "2025-07-26T10:30:00Z"
        }
    except Exception as e:
        logger.error(f"❌ Agent orchestration status check failed: {e}")
        return {
            "agent_orchestration": {
                "orchestration_available": False,
                "error": str(e)
            },
            "timestamp": "2025-07-26T10:30:00Z"
        }

@receipt_router.get("/document-ai/status")
async def get_document_ai_status():
    """Get Document AI service status"""
    try:
        status = await document_ai_service.get_processing_stats()
        return {
            "document_ai": status,
            "timestamp": "2025-07-26T10:30:00Z"
        }
    except Exception as e:
        logger.error(f"❌ Document AI status check failed: {e}")
        return {
            "document_ai": {
                "document_ai_available": False,
                "error": str(e)
            },
            "timestamp": "2025-07-26T10:30:00Z"
        }

@receipt_router.post("/query/orchestrated", response_model=QueryResponse)
async def process_orchestrated_query(request: QueryRequest):
    """Process query using agent orchestration"""
    try:
        logger.info(f"🤖 Processing orchestrated query: {request.query[:100]}...")
        
        # Use agent orchestration service
        response = await agent_orchestration_service.process_complex_query(request)
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Orchestrated query processing failed: {e}")
        return QueryResponse(
            answer="I encountered an error while processing your request with our AI agents. Please try again.",
            confidence=0.0,
            query_type=QueryType.GENERAL,
            detected_language=request.language or 'en',
            sources=[],
            actionable_items=[],
            can_create_wallet_pass=False,
            suggested_actions=["Try rephrasing your question", "Contact support if issue persists"]
        )
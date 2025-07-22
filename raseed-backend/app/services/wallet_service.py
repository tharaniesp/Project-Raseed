# app/services/wallet_service.py
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.core.config import settings
from app.services.receipt_service import ReceiptService
from app.models.receipt import ReceiptResponse
from app.core.database import get_firestore_client, is_firebase_initialized
from app.models.receipt import ReceiptUpdate
import datetime
import uuid
import logging
import json
import os

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/wallet_object.issuer"]

class WalletService:
    
    @staticmethod
    def is_wallet_available() -> bool:
        """Check if Google Wallet API is available"""
        try:
            # Check if service account file exists
            if not os.path.exists(settings.FIREBASE_SERVICE_ACCOUNT_PATH):
                logger.warning("❌ Firebase service account file not found")
                return False
            
            # Check if project ID is set
            if not settings.FIREBASE_PROJECT_ID:
                logger.warning("❌ Firebase project ID not set")
                return False
            
            return True
        except Exception as e:
            logger.error(f"❌ Wallet availability check failed: {e}")
            return False

    @staticmethod
    def get_wallet_client():
        """Initialize Google Wallet API client"""
        try:
            # Load service account credentials
            if os.path.exists(settings.FIREBASE_SERVICE_ACCOUNT_PATH):
                creds = service_account.Credentials.from_service_account_file(
                    settings.FIREBASE_SERVICE_ACCOUNT_PATH, scopes=SCOPES
                )
            else:
                # Try environment variables
                if settings.FIREBASE_PRIVATE_KEY and settings.FIREBASE_CLIENT_EMAIL:
                    cred_dict = {
                        "type": "service_account",
                        "project_id": settings.FIREBASE_PROJECT_ID,
                        "private_key": settings.FIREBASE_PRIVATE_KEY.replace('\\n', '\n'),
                        "client_email": settings.FIREBASE_CLIENT_EMAIL,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                    creds = service_account.Credentials.from_service_account_info(
                        cred_dict, scopes=SCOPES
                    )
                else:
                    raise Exception("No valid service account credentials found")
            
            service = build('walletobjects', 'v1', credentials=creds)
            logger.info("✅ Google Wallet client initialized successfully")
            return service
        except Exception as e:
            logger.error(f"❌ Failed to initialize Wallet client: {e}")
            raise Exception(f"Wallet client initialization failed: {str(e)}")
    
    @staticmethod
    def get_issuer_id():
        """Get the issuer ID for Google Wallet
        
        For Google Wallet, the issuer ID should be either:
        1. Project number (recommended)
        2. Project ID
        3. Custom issuer ID from Google Pay Console
        """
        # Try to get issuer ID from settings first
        if hasattr(settings, 'GOOGLE_WALLET_ISSUER_ID') and settings.GOOGLE_WALLET_ISSUER_ID:
            return settings.GOOGLE_WALLET_ISSUER_ID
        
        # Fall back to project ID, but clean it for wallet compatibility
        project_id = settings.FIREBASE_PROJECT_ID
        # Remove special characters that might cause issues
        return project_id.replace('-', '_').replace('.', '_')

    @staticmethod
    async def generate_pass_for_receipt(receipt_id: str) -> dict:
        """Generate Google Wallet pass for a receipt"""
        logger.info(f"🎫 Starting Wallet pass generation for receipt: {receipt_id}")

        # Check availability first
        if not WalletService.is_wallet_available():
            raise Exception("Google Wallet API not available - check configuration")

        # Step 1: Get receipt and validate data
        try:
            receipt: ReceiptResponse = await ReceiptService.get_receipt_by_id(receipt_id)
            if not receipt:
                raise Exception(f"Receipt not found: {receipt_id}")
            
            if not receipt.extracted_data:
                raise Exception(f"Receipt {receipt_id} has no extracted data - process with AI first")
            
            logger.info(f"✅ Receipt validated. Merchant: {receipt.extracted_data.merchant_name}")
        except Exception as e:
            logger.error(f"❌ Receipt validation failed: {e}")
            raise

        # Step 2: Initialize Wallet client
        try:
            wallet_service = WalletService.get_wallet_client()
            logger.info("✅ Wallet service client ready")
        except Exception as e:
            logger.error(f"❌ Wallet client initialization failed: {e}")
            raise

        # Step 3: Build class and object IDs with proper format
        issuer_id = WalletService.get_issuer_id()
        
        # Google Wallet class ID format: issuerID.classId
        # Class suffix should be descriptive and unique
        class_suffix = "raseed_receipt_class"
        class_id = f"{issuer_id}.{class_suffix}"
        
        # Object ID format: issuerID.objectId  
        # Object suffix should be unique per receipt
        object_suffix = f"receipt_{receipt_id}_{uuid.uuid4().hex[:8]}"
        object_id = f"{issuer_id}.{object_suffix}"
        
        logger.info(f"📝 Issuer ID: {issuer_id}")
        logger.info(f"📝 Class ID: {class_id}")
        logger.info(f"📝 Object ID: {object_id}")

        # Step 4: Ensure the Wallet class exists
        try:
            # Try to get existing class
            existing_class = wallet_service.genericclass().get(resourceId=class_id).execute()
            logger.info(f"📦 Using existing Wallet class: {class_id}")
        except HttpError as e:
            if e.resp.status == 404:
                # Class doesn't exist, create it
                logger.info(f"📦 Creating new Wallet class: {class_id}")
                
                class_payload = {
                    "id": class_id,
                    "issuerName": "Project Raseed",
                    "reviewStatus": "UNDER_REVIEW",
                    "hexBackgroundColor": "#4285F4",
                    "callbackOptions": {
                        "updateRequestUrl": f"https://your-app.com/api/wallet/callback",
                        "url": f"https://your-app.com/receipts/{receipt_id}"
                    }
                }
                
                try:
                    create_response = wallet_service.genericclass().insert(body=class_payload).execute()
                    logger.info(f"✅ Wallet class created successfully: {create_response.get('id')}")
                except Exception as create_error:
                    logger.error(f"❌ Failed to create Wallet class: {create_error}")
                    # Log the full error details
                    if hasattr(create_error, 'content'):
                        logger.error(f"❌ Error details: {create_error.content}")
                    raise Exception(f"Could not create Wallet class: {str(create_error)}")
            else:
                logger.error(f"❌ Error checking Wallet class: {e}")
                # Log more details about the error
                if hasattr(e, 'content'):
                    logger.error(f"❌ Error details: {e.content}")
                    
                # If it's a 400 error, it might be an issuer ID issue
                if e.resp.status == 400:
                    raise Exception(f"Invalid class ID format. Check your issuer ID configuration. Class ID: {class_id}")
                    
                raise Exception(f"Wallet class check failed: {str(e)}")

        # Step 5: Prepare pass data
        extracted = receipt.extracted_data
        
        # Format items for display
        items_list = []
        if extracted.items and len(extracted.items) > 0:
            for item in extracted.items[:5]:  # Limit to first 5 items
                price_str = f"${item.total_price:.2f}" if item.total_price else "N/A"
                items_list.append(f"• {item.name}: {price_str}")
            
            if len(extracted.items) > 5:
                items_list.append(f"... and {len(extracted.items) - 5} more items")
        else:
            items_list.append("• No items extracted")
        
        items_text = "\n".join(items_list)
        
        # Format receipt summary
        total_amount = f"${extracted.total_amount:.2f}" if extracted.total_amount else "N/A"
        tax_amount = f"${extracted.tax_amount:.2f}" if extracted.tax_amount else "N/A"
        receipt_date = extracted.receipt_date or "Unknown date"
        
        # Step 6: Create the Wallet object (pass)
        object_payload = {
            "id": object_id,
            "classId": class_id,
            "state": "ACTIVE",
            
            "cardTitle": {
                "defaultValue": {
                    "language": "en-US",
                    "value": f"Receipt - {extracted.merchant_name or 'Store'}"
                }
            },
            
            "header": {
                "defaultValue": {
                    "language": "en-US", 
                    "value": extracted.merchant_name or "Receipt"
                }
            },
            
            "subheader": {
                "defaultValue": {
                    "language": "en-US",
                    "value": f"Total: {total_amount} • {receipt_date}"
                }
            },
            
            "textModulesData": [
                {
                    "header": "Receipt Summary",
                    "body": f"Date: {receipt_date}\nTotal: {total_amount}\nTax: {tax_amount}\nItems: {len(extracted.items) if extracted.items else 0}"
                },
                {
                    "header": "Items Purchased",
                    "body": items_text
                }
            ],
            
            "linksModuleData": {
                "uris": [
                    {
                        "uri": f"https://your-app.com/receipts/{receipt_id}",
                        "description": "View in Project Raseed"
                    }
                ]
            },
            
            # Use the receipt image from Firebase Storage
            "heroImage": {
                "sourceUri": {
                    "uri": receipt.download_url  # This is the Firebase Storage URL
                },
                "contentDescription": {
                    "defaultValue": {
                        "language": "en-US", 
                        "value": "Receipt Image"
                    }
                }
            },
            
            "hexBackgroundColor": "#4285F4",
            "barcode": {
                "type": "QR_CODE",
                "value": f"raseed://receipt/{receipt_id}",
                "alternateText": f"Receipt ID: {receipt_id}"
            }
        }

        # Step 7: Create the pass object
        try:
            logger.info(f"🎫 Creating Wallet object: {object_id}")
            response = wallet_service.genericobject().insert(body=object_payload).execute()
            logger.info(f"✅ Wallet pass created successfully: {response['id']}")
        except HttpError as e:
            error_details = e.content.decode() if hasattr(e, 'content') else str(e)
            logger.error(f"❌ Wallet pass creation failed: {error_details}")
            raise Exception(f"Failed to create wallet pass: {error_details}")
        except Exception as e:
            logger.error(f"❌ Unexpected error creating wallet pass: {e}")
            raise Exception(f"Wallet pass creation error: {str(e)}")

        # Step 8: Save wallet info to Firestore
        if is_firebase_initialized():
            try:
                db = get_firestore_client()
                doc_ref = db.collection(settings.FIRESTORE_COLLECTION_RECEIPTS).document(receipt_id)
                
                # Check if document exists
                doc = doc_ref.get()
                if doc.exists:
                    update_data = {
                        "wallet_object_id": response["id"],
                        "wallet_state": response.get("state", "ACTIVE"),
                        "wallet_created_at": datetime.datetime.utcnow(),
                        "wallet_save_url": f"https://pay.google.com/gp/v/save/{response['id']}"
                    }
                    doc_ref.update(update_data)
                    logger.info("✅ Firestore updated with wallet pass info")
                else:
                    logger.warning(f"⚠️ Firestore document not found for receipt: {receipt_id}")
            except Exception as e:
                logger.error(f"❌ Firestore update failed: {e}")
                # Don't fail the whole process if Firestore update fails

        # Step 9: Generate and return save URL
        save_url = f"https://pay.google.com/gp/v/save/{response['id']}"
        
        result = {
            "save_url": save_url,
            "object_id": response["id"],
            "class_id": class_id,
            "wallet_state": response.get("state", "ACTIVE")
        }
        
        logger.info(f"🎉 Wallet pass generation completed successfully!")
        logger.info(f"🔗 Save URL: {save_url}")
        
        return result

    @staticmethod
    async def get_pass_status_by_receipt(receipt_id: str) -> dict:
        """Get Google Wallet pass status for a receipt"""
        try:
            # Get receipt from database
            receipt = await ReceiptService.get_receipt_by_id(receipt_id)
            if not receipt:
                return {"status": "receipt_not_found"}
            
            # Check if wallet pass was created
            if not hasattr(receipt, 'wallet_object_id') or not receipt.wallet_object_id:
                return {"status": "pass_not_created"}
            
            # Check wallet service availability
            if not WalletService.is_wallet_available():
                return {"status": "wallet_service_unavailable"}
            
            # Get pass status from Google Wallet API
            wallet_service = WalletService.get_wallet_client()
            
            try:
                wallet_object = wallet_service.genericobject().get(
                    resourceId=receipt.wallet_object_id
                ).execute()
                
                return {
                    "status": "success",
                    "wallet_state": wallet_object.get("state", "UNKNOWN"),
                    "object_id": wallet_object.get("id"),
                    "has_users": wallet_object.get("hasUsers", False),
                    "save_url": f"https://pay.google.com/gp/v/save/{wallet_object.get('id')}"
                }
            except HttpError as e:
                if e.resp.status == 404:
                    return {"status": "pass_not_found"}
                else:
                    logger.error(f"❌ Wallet API error: {e}")
                    return {"status": "api_error", "error": str(e)}
                    
        except Exception as e:
            logger.error(f"❌ Failed to get pass status: {e}")
            return {"status": "error", "error": str(e)}
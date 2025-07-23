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
import jwt
import time

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
        """Get the issuer ID for Google Wallet"""
        # Try to get issuer ID from settings first
        if hasattr(settings, 'GOOGLE_WALLET_ISSUER_ID') and settings.GOOGLE_WALLET_ISSUER_ID:
            return settings.GOOGLE_WALLET_ISSUER_ID
        
        # Fall back to project ID, but clean it for wallet compatibility
        project_id = settings.FIREBASE_PROJECT_ID
        # Remove special characters that might cause issues
        return project_id.replace('-', '_').replace('.', '_')

    @staticmethod
    def get_service_account_credentials():
        """Get service account credentials for JWT signing"""
        try:
            if os.path.exists(settings.FIREBASE_SERVICE_ACCOUNT_PATH):
                with open(settings.FIREBASE_SERVICE_ACCOUNT_PATH, 'r') as f:
                    service_account_info = json.load(f)
                return service_account_info
            else:
                # Try environment variables
                if settings.FIREBASE_PRIVATE_KEY and settings.FIREBASE_CLIENT_EMAIL:
                    return {
                        "type": "service_account",
                        "project_id": settings.FIREBASE_PROJECT_ID,
                        "private_key": settings.FIREBASE_PRIVATE_KEY.replace('\\n', '\n'),
                        "client_email": settings.FIREBASE_CLIENT_EMAIL,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                else:
                    raise Exception("No valid service account credentials found")
        except Exception as e:
            logger.error(f"❌ Failed to get service account credentials: {e}")
            raise

    @staticmethod
    async def ensure_generic_class_exists(wallet_service, class_id: str):
        """Ensure the generic class exists, create if it doesn't"""
        try:
            # Try to get existing class
            existing_class = wallet_service.genericclass().get(resourceId=class_id).execute()
            logger.info(f"📦 Using existing Generic class: {class_id}")
            return existing_class
        except HttpError as e:
            if e.resp.status == 404:
                # Class doesn't exist, create it
                logger.info(f"📦 Creating new Generic class: {class_id}")
                
                class_payload = {
                    "id": class_id,
                    "issuerName": "Project Raseed",
                    "reviewStatus": "UNDER_REVIEW",
                    "hexBackgroundColor": "#4285F4",
                    "logo": {
                        "sourceUri": {
                            "uri": "https://your-app.com/logo.png"  # Replace with your actual logo URL
                        },
                        "contentDescription": {
                            "defaultValue": {
                                "language": "en-US",
                                "value": "Project Raseed Logo"
                            }
                        }
                    }
                }
                
                try:
                    create_response = wallet_service.genericclass().insert(body=class_payload).execute()
                    logger.info(f"✅ Generic class created successfully: {create_response.get('id')}")
                    return create_response
                except Exception as create_error:
                    logger.error(f"❌ Failed to create Generic class: {create_error}")
                    raise Exception(f"Could not create Generic class: {str(create_error)}")
            else:
                logger.error(f"❌ Error checking Generic class: {e}")
                raise Exception(f"Generic class check failed: {str(e)}")

    @staticmethod
    def create_minimal_jwt(object_id: str, class_id: str, service_account_info: dict):
        """Create a minimal JWT to stay under 1800 character limit"""
        try:
            # Minimal payload - only reference the object, don't include full definitions
            payload = {
                "iss": service_account_info["client_email"],
                "aud": "google",
                "typ": "savetowallet",
                "iat": int(time.time()),
                "origins": ["localhost"],  # Add your actual domain
                "payload": {
                    "genericObjects": [
                        {
                            "id": object_id
                        }
                    ]
                }
            }
            
            # Sign JWT with private key
            private_key = service_account_info["private_key"]
            signed_jwt = jwt.encode(payload, private_key, algorithm="RS256")
            
            logger.info(f"✅ Minimal JWT created. Length: {len(signed_jwt)} characters")
            
            if len(signed_jwt) > 1800:
                logger.warning(f"⚠️ JWT length ({len(signed_jwt)}) exceeds recommended 1800 characters")
            
            return signed_jwt
            
        except Exception as e:
            logger.error(f"❌ JWT creation failed: {e}")
            raise Exception(f"JWT creation failed: {str(e)}")

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
        
        # Using Generic pass type (better for receipts than loyalty)
        class_suffix = "raseed_receipt_generic_class"
        class_id = f"{issuer_id}.{class_suffix}"
        
        object_suffix = f"receipt_{receipt_id}_{uuid.uuid4().hex[:8]}"
        object_id = f"{issuer_id}.{object_suffix}"
        
        logger.info(f"📝 Issuer ID: {issuer_id}")
        logger.info(f"📝 Class ID: {class_id}")
        logger.info(f"📝 Object ID: {object_id}")

        # Step 4: Ensure the class exists (pre-create it)
        try:
            await WalletService.ensure_generic_class_exists(wallet_service, class_id)
        except Exception as e:
            logger.error(f"❌ Class creation/verification failed: {e}")
            raise

        # Step 5: Prepare pass data
        extracted = receipt.extracted_data
        
        # Format items for display (keep it concise)
        items_summary = ""
        if extracted.items and len(extracted.items) > 0:
            first_item = extracted.items[0]
            price_str = f"${first_item.total_price:.2f}" if first_item.total_price else ""
            items_summary = f"{first_item.name} {price_str}"
            if len(extracted.items) > 1:
                items_summary += f" (+{len(extracted.items) - 1} more)"
        
        # Format receipt summary
        total_amount = f"${extracted.total_amount:.2f}" if extracted.total_amount else "N/A"
        receipt_date = extracted.receipt_date or "Unknown date"

        # Step 6: Create the Generic Object (minimal version)
        generic_object = {
            "id": object_id,
            "classId": class_id,
            "state": "ACTIVE",
            "genericType": "GENERIC_TYPE_UNSPECIFIED",
            
            "cardTitle": {
                "defaultValue": {
                    "language": "en-US",
                    "value": f"{extracted.merchant_name or 'Receipt'}"
                }
            },
            
            "header": {
                "defaultValue": {
                    "language": "en-US", 
                    "value": f"Total: {total_amount}"
                }
            },
            
            "subheader": {
                "defaultValue": {
                    "language": "en-US",
                    "value": receipt_date
                }
            },
            
            "textModulesData": [
                {
                    "header": "Items",
                    "body": items_summary or "Receipt items",
                    "id": "items"
                }
            ],
            
            "barcode": {
                "type": "QR_CODE",
                "value": f"raseed://receipt/{receipt_id}",
                "alternateText": receipt_id[:8]
            },
            
            "hexBackgroundColor": "#4285F4"
        }

        # Step 7: Create the object via API first (not in JWT)
        try:
            logger.info(f"🎫 Creating Generic object: {object_id}")
            response = wallet_service.genericobject().insert(body=generic_object).execute()
            logger.info(f"✅ Generic object created successfully: {response['id']}")
        except HttpError as e:
            error_details = e.content.decode() if hasattr(e, 'content') else str(e)
            logger.error(f"❌ Generic object creation failed: {error_details}")
            raise Exception(f"Failed to create wallet object: {error_details}")

        # Step 8: Create minimal JWT (only references the object)
        try:
            logger.info("🔐 Creating minimal JWT...")
            service_account_info = WalletService.get_service_account_credentials()
            signed_jwt = WalletService.create_minimal_jwt(object_id, class_id, service_account_info)
            logger.info("✅ Minimal JWT signed successfully")
        except Exception as e:
            logger.error(f"❌ JWT creation failed: {e}")
            raise Exception(f"Failed to create signed JWT: {str(e)}")

        # Step 9: Save wallet info to Firestore
        if is_firebase_initialized():
            try:
                db = get_firestore_client()
                doc_ref = db.collection(settings.FIRESTORE_COLLECTION_RECEIPTS).document(receipt_id)
                
                # Check if document exists
                doc = doc_ref.get()
                if doc.exists:
                    update_data = {
                        "wallet_object_id": object_id,
                        "wallet_class_id": class_id,
                        "wallet_state": "ACTIVE",
                        "wallet_created_at": datetime.datetime.utcnow(),
                        "wallet_jwt_length": len(signed_jwt)
                    }
                    doc_ref.update(update_data)
                    logger.info("✅ Firestore updated with wallet pass info")
                else:
                    logger.warning(f"⚠️ Firestore document not found for receipt: {receipt_id}")
            except Exception as e:
                logger.error(f"❌ Firestore update failed: {e}")
                # Don't fail the whole process if Firestore update fails

        # Step 10: Generate save URL with signed JWT
        save_url = f"https://pay.google.com/gp/v/save/{signed_jwt}"
        
        result = {
            "save_url": save_url,
            "object_id": object_id,
            "class_id": class_id,
            "wallet_state": "ACTIVE",
            "jwt_length": len(signed_jwt)
        }
        
        logger.info(f"🎉 Wallet pass generation completed successfully!")
        logger.info(f"🔗 Save URL: {save_url}")
        logger.info(f"📏 JWT Length: {len(signed_jwt)} characters")
        
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
                # Use genericobject for generic passes
                wallet_object = wallet_service.genericobject().get(
                    resourceId=receipt.wallet_object_id
                ).execute()
                
                return {
                    "status": "success",
                    "wallet_state": wallet_object.get("state", "UNKNOWN"),
                    "object_id": wallet_object.get("id"),
                    "has_users": wallet_object.get("hasUsers", False)
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
# app/services/wallet_service.py - Enhanced version with all items
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
    def format_items_for_wallet(items: list, max_length: int = 800) -> list:
        """Format items for wallet pass with smart truncation"""
        if not items:
            return [{"header": "Items", "body": "No items found", "id": "items"}]
        
        # Strategy 1: Try to fit all items
        all_items_text = ""
        for i, item in enumerate(items):
            price_str = f" - ${item.total_price:.2f}" if item.total_price else ""
            quantity_str = f"{item.quantity}x " if item.quantity and item.quantity > 1 else ""
            item_line = f"{quantity_str}{item.name}{price_str}"
            
            if i == 0:
                all_items_text = item_line
            else:
                all_items_text += f"\n{item_line}"
        
        # If all items fit, return them
        if len(all_items_text) <= max_length:
            return [{
                "header": f"Items ({len(items)})",
                "body": all_items_text,
                "id": "items"
            }]
        
        # Strategy 2: Smart truncation with most important items
        truncated_text = ""
        items_shown = 0
        
        for item in items:
            price_str = f" - ${item.total_price:.2f}" if item.total_price else ""
            quantity_str = f"{item.quantity}x " if item.quantity and item.quantity > 1 else ""
            item_line = f"{quantity_str}{item.name}{price_str}"
            
            test_text = truncated_text + ("\n" if truncated_text else "") + item_line
            
            # Reserve space for "... and X more items"
            remaining_items = len(items) - items_shown - 1
            footer_text = f"\n... and {remaining_items} more items" if remaining_items > 0 else ""
            
            if len(test_text + footer_text) <= max_length:
                truncated_text = test_text
                items_shown += 1
            else:
                break
        
        # Add footer if there are more items
        if items_shown < len(items):
            remaining = len(items) - items_shown
            truncated_text += f"\n... and {remaining} more items"
        
        return [{
            "header": f"Items ({len(items)} total, showing {items_shown})",
            "body": truncated_text,
            "id": "items"
        }]
    
    @staticmethod
    def create_enhanced_wallet_object(receipt: ReceiptResponse, object_id: str, class_id: str) -> dict:
        """Create enhanced wallet object with better item display"""
        extracted = receipt.extracted_data
        
        # Enhanced items formatting
        items_modules = []
        if extracted.items and len(extracted.items) > 0:
            # Try multiple text modules for better organization
            if len(extracted.items) <= 5:
                # Show all items in one module
                items_modules = WalletService.format_items_for_wallet(extracted.items)
            else:
                # Split into multiple modules for better readability
                # First module: Primary items (first 3-4)
                primary_items = extracted.items[:4]
                items_modules.extend(WalletService.format_items_for_wallet(primary_items, 400))
                
                # Second module: Additional items if there are more
                if len(extracted.items) > 4:
                    additional_items = extracted.items[4:]
                    additional_modules = WalletService.format_items_for_wallet(additional_items, 400)
                    # Update header for additional items
                    for module in additional_modules:
                        module["header"] = f"More Items ({len(additional_items)})"
                        module["id"] = "additional_items"
                    items_modules.extend(additional_modules)
        else:
            items_modules = [{"header": "Items", "body": "No items extracted", "id": "items"}]
        
        # Add receipt summary module
        summary_parts = []
        if extracted.subtotal:
            summary_parts.append(f"Subtotal: ${extracted.subtotal:.2f}")
        if extracted.tax_amount:
            summary_parts.append(f"Tax: ${extracted.tax_amount:.2f}")
        if extracted.total_amount:
            summary_parts.append(f"Total: ${extracted.total_amount:.2f}")
        if extracted.payment_method:
            summary_parts.append(f"Payment: {extracted.payment_method}")
        
        summary_text = "\n".join(summary_parts) if summary_parts else "Receipt summary"
        
        # Enhanced wallet object
        wallet_object = {
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
                    "value": f"${extracted.total_amount:.2f}" if extracted.total_amount else "Receipt"
                }
            },
            
            "subheader": {
                "defaultValue": {
                    "language": "en-US",
                    "value": f"{extracted.receipt_date or 'Unknown date'} • {extracted.merchant_address or 'Store location'}"[:50]
                }
            },
            
            # Multiple text modules for better organization
            "textModulesData": items_modules + [
                {
                    "header": "Receipt Summary",
                    "body": summary_text,
                    "id": "summary"
                }
            ],
            
            "barcode": {
                "type": "QR_CODE",
                "value": f"raseed://receipt/{receipt.id}",
                "alternateText": receipt.id[:8]
            },
            
            "hexBackgroundColor": "#4285F4",
            
            # Add links section for more details
            "linksModuleData": {
                "uris": [
                    {
                        "uri": f"http://localhost:3000/query",
                        "description": "Chat with Personal Assistant",
                        "id": "receipt_details"
                    }
                ]
            }
        }
        
        return wallet_object
    
    @staticmethod
    async def generate_pass_for_receipt(receipt_id: str) -> dict:
        """Generate Google Wallet pass with enhanced item display"""
        logger.info(f"🎫 Starting enhanced Wallet pass generation for receipt: {receipt_id}")

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
            
            logger.info(f"✅ Receipt validated. Items count: {len(receipt.extracted_data.items) if receipt.extracted_data.items else 0}")
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

        # Step 3: Build class and object IDs
        issuer_id = WalletService.get_issuer_id()
        class_suffix = "raseed_receipt_enhanced_class"
        class_id = f"{issuer_id}.{class_suffix}"
        object_suffix = f"receipt_{receipt_id}_{uuid.uuid4().hex[:8]}"
        object_id = f"{issuer_id}.{object_suffix}"
        
        logger.info(f"📝 Creating enhanced pass with {len(receipt.extracted_data.items) if receipt.extracted_data.items else 0} items")

        # Step 4: Ensure the class exists
        try:
            await WalletService.ensure_generic_class_exists(wallet_service, class_id)
        except Exception as e:
            logger.error(f"❌ Class creation/verification failed: {e}")
            raise

        # Step 5: Create enhanced wallet object
        try:
            enhanced_object = WalletService.create_enhanced_wallet_object(receipt, object_id, class_id)
            logger.info(f"📦 Enhanced wallet object created with {len(enhanced_object['textModulesData'])} text modules")
        except Exception as e:
            logger.error(f"❌ Enhanced object creation failed: {e}")
            raise

        # Step 6: Create the object via API
        try:
            logger.info(f"🎫 Creating enhanced Generic object: {object_id}")
            response = wallet_service.genericobject().insert(body=enhanced_object).execute()
            logger.info(f"✅ Enhanced Generic object created successfully")
        except HttpError as e:
            error_details = e.content.decode() if hasattr(e, 'content') else str(e)
            logger.error(f"❌ Enhanced object creation failed: {error_details}")
            raise Exception(f"Failed to create enhanced wallet object: {error_details}")

        # Step 7: Create minimal JWT
        try:
            logger.info("🔐 Creating JWT for enhanced pass...")
            service_account_info = WalletService.get_service_account_credentials()
            signed_jwt = WalletService.create_minimal_jwt(object_id, class_id, service_account_info)
            logger.info("✅ Enhanced pass JWT signed successfully")
        except Exception as e:
            logger.error(f"❌ JWT creation failed: {e}")
            raise Exception(f"Failed to create signed JWT: {str(e)}")

        # Step 8: Save to Firestore
        if is_firebase_initialized():
            try:
                db = get_firestore_client()
                doc_ref = db.collection(settings.FIRESTORE_COLLECTION_RECEIPTS).document(receipt_id)
                doc = doc_ref.get()
                if doc.exists:
                    update_data = {
                        "wallet_object_id": object_id,
                        "wallet_class_id": class_id,
                        "wallet_state": "ACTIVE",
                        "wallet_created_at": datetime.datetime.utcnow(),
                        "wallet_jwt_length": len(signed_jwt),
                        "wallet_items_count": len(receipt.extracted_data.items) if receipt.extracted_data.items else 0
                    }
                    doc_ref.update(update_data)
                    logger.info("✅ Firestore updated with enhanced wallet pass info")
            except Exception as e:
                logger.error(f"❌ Firestore update failed: {e}")

        # Step 9: Generate save URL
        save_url = f"https://pay.google.com/gp/v/save/{signed_jwt}"
        
        result = {
            "save_url": save_url,
            "object_id": object_id,
            "class_id": class_id,
            "wallet_state": "ACTIVE",
            "jwt_length": len(signed_jwt),
            "items_included": len(receipt.extracted_data.items) if receipt.extracted_data.items else 0
        }
        
        logger.info(f"🎉 Enhanced wallet pass generation completed!")
        logger.info(f"📊 Items included: {result['items_included']}")
        
        return result

    # Keep all other existing methods unchanged...
    @staticmethod
    def is_wallet_available() -> bool:
        """Check if Google Wallet API is available"""
        try:
            if not os.path.exists(settings.FIREBASE_SERVICE_ACCOUNT_PATH):
                logger.warning("❌ Firebase service account file not found")
                return False
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
            if os.path.exists(settings.FIREBASE_SERVICE_ACCOUNT_PATH):
                creds = service_account.Credentials.from_service_account_file(
                    settings.FIREBASE_SERVICE_ACCOUNT_PATH, scopes=SCOPES
                )
            else:
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
        if hasattr(settings, 'GOOGLE_WALLET_ISSUER_ID') and settings.GOOGLE_WALLET_ISSUER_ID:
            return settings.GOOGLE_WALLET_ISSUER_ID
        project_id = settings.FIREBASE_PROJECT_ID
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
            existing_class = wallet_service.genericclass().get(resourceId=class_id).execute()
            logger.info(f"📦 Using existing Generic class: {class_id}")
            return existing_class
        except HttpError as e:
            if e.resp.status == 404:
                logger.info(f"📦 Creating new Generic class: {class_id}")
                class_payload = {
                    "id": class_id,
                    "issuerName": "Project Raseed",
                    "reviewStatus": "UNDER_REVIEW",
                    "hexBackgroundColor": "#4285F4",
                    "logo": {
                        "sourceUri": {
                            "uri": "https://your-app.com/logo.png"
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
            payload = {
                "iss": service_account_info["client_email"],
                "aud": "google",
                "typ": "savetowallet",
                "iat": int(time.time()),
                "origins": ["localhost"],
                "payload": {
                    "genericObjects": [{"id": object_id}]
                }
            }
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
    def create_jwt(generic_object: dict, object_id: str):
        """Create JWT for Google Wallet object with more comprehensive approach"""
        try:
            # Get credentials for JWT signing
            service_account_info = WalletService.get_service_account_credentials()
            
            # Create a minimal JWT to ensure we stay under size limits
            payload = {
                "iss": service_account_info["client_email"],
                "aud": "google",
                "typ": "savetowallet",
                "iat": int(time.time()),
                "origins": ["localhost"],
                "payload": {
                    "genericObjects": [{"id": object_id}]
                }
            }
            
            private_key = service_account_info["private_key"]
            signed_jwt = jwt.encode(payload, private_key, algorithm="RS256")
            
            logger.info(f"✅ JWT created for object {object_id}. Length: {len(signed_jwt)} characters")
            
            # Check JWT length
            if len(signed_jwt) > 1800:
                logger.warning(f"⚠️ JWT length ({len(signed_jwt)}) exceeds recommended 1800 characters")
                
            return signed_jwt
        except Exception as e:
            logger.error(f"❌ JWT creation failed: {e}")
            raise Exception(f"JWT creation failed: {str(e)}")

    @staticmethod
    async def get_pass_status_by_receipt(receipt_id: str) -> dict:
        """Get Google Wallet pass status for a receipt"""
        try:
            receipt = await ReceiptService.get_receipt_by_id(receipt_id)
            if not receipt:
                return {"status": "receipt_not_found"}
            
            if not hasattr(receipt, 'wallet_object_id') or not receipt.wallet_object_id:
                return {"status": "pass_not_created"}
            
            if not WalletService.is_wallet_available():
                return {"status": "wallet_service_unavailable"}
            
            wallet_service = WalletService.get_wallet_client()
            
            try:
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
    
    @staticmethod
    async def create_shopping_list_pass(title: str, items: list, estimated_total: float = None, metadata: dict = None) -> dict:
        """Create a Google Wallet pass specifically for shopping lists"""
        try:
            logger.info(f"🛒 Creating shopping list wallet pass: {title}")
            
            # Check if wallet service is available
            if not WalletService.is_wallet_available():
                raise Exception("Google Wallet service not available")
            
            # Generate unique identifiers
            class_suffix = f"shopping_list_{int(time.time())}"
            object_suffix = f"list_{uuid.uuid4().hex[:8]}"
            
            issuer_id = WalletService.get_issuer_id()
            class_id = f"{issuer_id}.{class_suffix}"
            object_id = f"{issuer_id}.{object_suffix}"
            
            # Create shopping list specific content
            shopping_items_text = []
            for i, item in enumerate(items, 1):
                quantity = item.get('quantity', '1')
                name = item.get('name', 'Unknown Item')
                category = item.get('category', '')
                
                item_line = f"{i}. {quantity}x {name}"
                if category:
                    item_line += f" ({category})"
                shopping_items_text.append(item_line)
            
            # Create generic class for shopping list
            generic_class = {
                "id": class_id,
                "classTemplateInfo": {
                    "cardTemplateOverride": {
                        "cardRowTemplateInfos": [
                            {
                                "twoItems": {
                                    "startItem": {
                                        "firstValue": {
                                            "fields": [
                                                {
                                                    "fieldPath": "object.textModulesData['items']"
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            }
            
            # Create generic object for shopping list
            generic_object = {
                "id": object_id,
                "classId": class_id,
                "state": "ACTIVE",
                # Using a more reliable logo approach like in other wallet objects
                "hexBackgroundColor": "#4285F4",
                "cardTitle": {
                    "defaultValue": {
                        "language": "en-US", 
                        "value": title
                    }
                },
                "subheader": {
                    "defaultValue": {
                        "language": "en-US",
                        "value": f"{len(items)} items"
                    }
                },
                "header": {
                    "defaultValue": {
                        "language": "en-US",
                        "value": "Shopping List"
                    }
                },
                "textModulesData": [
                    {
                        "id": "items",
                        "header": "Items to Buy",
                        "body": "\n".join(shopping_items_text)
                    }
                ],
                "linksModuleData": {
                    "uris": []
                }
            }
            
            # Add estimated total if provided
            if estimated_total:
                generic_object["textModulesData"].append({
                    "id": "total",
                    "header": "Estimated Total",
                    "body": f"${estimated_total:.2f}"
                })
            
            # Add metadata if provided
            if metadata:
                generic_object["textModulesData"].append({
                    "id": "metadata",
                    "header": "Generated",
                    "body": f"Query ID: {metadata.get('query_id', 'N/A')}\nLanguage: {metadata.get('detected_language', 'en')}"
                })
            
            # Get wallet client
            wallet_service = WalletService.get_wallet_client()
            
            # Create or update the class
            try:
                wallet_service.genericclass().insert(body=generic_class).execute()
                logger.info(f"✅ Created shopping list class: {class_id}")
            except HttpError as e:
                if e.resp.status == 409:  # Already exists
                    logger.info(f"📋 Shopping list class already exists: {class_id}")
                else:
                    logger.warning(f"⚠️ Error creating class, will try to continue: {str(e)}")
            
            # Create the object
            try:
                wallet_service.genericobject().insert(body=generic_object).execute()
                logger.info(f"✅ Created shopping list object: {object_id}")
            except HttpError as e:
                if e.resp.status == 409:  # Already exists
                    try:
                        wallet_service.genericobject().update(
                            resourceId=object_id, 
                            body=generic_object
                        ).execute()
                        logger.info(f"📝 Updated existing shopping list object: {object_id}")
                    except Exception as update_error:
                        logger.error(f"❌ Failed to update existing object: {update_error}")
                        raise Exception(f"Failed to update existing object: {str(update_error)}")
                else:
                    error_details = e.content.decode() if hasattr(e, 'content') else str(e)
                    logger.error(f"❌ Failed to create object: {error_details}")
                    raise Exception(f"Failed to create wallet object: {error_details}")
            
            # Generate signed JWT
            try:
                signed_jwt = WalletService.create_jwt(generic_object, object_id)
                save_url = f"https://pay.google.com/gp/v/save/{signed_jwt}"
                
                result = {
                    "save_url": save_url,
                    "object_id": object_id,
                    "class_id": class_id,
                    "wallet_state": "ACTIVE",
                    "items_count": len(items),
                    "estimated_total": estimated_total
                }
                
                logger.info(f"🎉 Shopping list wallet pass created successfully!")
                logger.info(f"🔗 Save URL: {save_url}")
                logger.info(f"📦 Items: {len(items)}")
                
                return result
            except Exception as jwt_error:
                logger.error(f"❌ JWT creation failed for shopping list, trying minimal JWT: {jwt_error}")
                # Fallback to minimal JWT
                service_account_info = WalletService.get_service_account_credentials()
                signed_jwt = WalletService.create_minimal_jwt(object_id, class_id, service_account_info)
                save_url = f"https://pay.google.com/gp/v/save/{signed_jwt}"
                
                result = {
                    "save_url": save_url,
                    "object_id": object_id,
                    "class_id": class_id,
                    "wallet_state": "ACTIVE",
                    "items_count": len(items),
                    "estimated_total": estimated_total,
                    "used_fallback": True
                }
                
                logger.info(f"🎉 Shopping list wallet pass created with fallback method!")
                return result
            
        except Exception as e:
            logger.error(f"❌ Shopping list wallet pass creation failed: {e}")
            raise e
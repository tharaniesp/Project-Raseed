# app/services/ai_service.py
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import requests
from PIL import Image
import io
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.config import settings
from app.models.receipt import ExtractedData, ExtractedItem

logger = logging.getLogger(__name__)

class AIService:
    """Service class for AI-powered receipt processing using Gemini Vision"""
    
    def __init__(self):
        """Initialize Gemini AI client"""
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("✅ Gemini AI initialized successfully")
        else:
            self.model = None
            logger.warning("⚠️ GEMINI_API_KEY not found - AI features disabled")
    
    def is_available(self) -> bool:
        """Check if AI service is available"""
        return self.model is not None
    
    async def download_image_from_url(self, image_url: str) -> Optional[Image.Image]:
        """Download and process image from Firebase Storage URL"""
        try:
            logger.info(f"📥 Downloading image from: {image_url}")
            
            # Download image
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Convert to PIL Image
            image_data = io.BytesIO(response.content)
            image = Image.open(image_data)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            logger.info(f"✅ Image downloaded successfully: {image.size}")
            return image
            
        except Exception as e:
            logger.error(f"❌ Failed to download image: {e}")
            return None
    
    def create_extraction_prompt(self) -> str:
        """Create the prompt for receipt data extraction"""
        return """
        You are an expert receipt data extractor. Analyze this receipt image and extract the following information in JSON format.

        Return ONLY a valid JSON object with this exact structure:

        {
            "merchant_name": "string - name of the store/restaurant",
            "merchant_address": "string - full address if visible",
            "receipt_date": "string - date in YYYY-MM-DD format",
            "receipt_time": "string - time in HH:MM format",
            "receipt_number": "string - receipt/transaction number",
            "payment_method": "string - cash, card, etc.",
            "currency": "string - currency code (USD, EUR, etc.)",
            "items": [
                {
                    "name": "string - item name",
                    "quantity": number - quantity (default 1),
                    "unit_price": number - price per unit,
                    "total_price": number - total for this item,
                    "category": "string - food, household, etc."
                }
            ],
            "subtotal": number - subtotal before tax,
            "tax_amount": number - tax amount,
            "total_amount": number - final total,
            "confidence_score": number - your confidence (0.0 to 1.0),
            "raw_text": "string - any additional text you see"
        }

        Rules:
        1. Extract ALL visible items with their prices
        2. Use null for missing fields
        3. Calculate confidence based on image clarity
        4. Include partial data even if some fields are unclear
        5. For prices, use decimal numbers (e.g., 12.99, not "$12.99")
        6. Guess reasonable categories for items
        7. Return only the JSON, no additional text
        """
    
    async def extract_receipt_data(self, image_url: str) -> Optional[ExtractedData]:
        """Extract structured data from receipt image using Gemini Vision"""
        if not self.is_available():
            logger.error("❌ Gemini AI not available")
            return None
        
        try:
            logger.info(f"🤖 Starting AI extraction for: {image_url}")
            
            # Download image
            image = await self.download_image_from_url(image_url)
            if not image:
                return None
            
            # Create prompt
            prompt = self.create_extraction_prompt()
            
            # Safety settings
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            # Generate content
            logger.info("🧠 Sending image to Gemini Vision...")
            response = self.model.generate_content(
                [prompt, image],
                safety_settings=safety_settings,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Low temperature for consistent extraction
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=2048,
                )
            )
            
            # Extract JSON from response
            raw_response = response.text.strip()
            logger.info(f"🤖 Raw AI response: {raw_response[:200]}...")
            
            # Clean and parse JSON
            json_str = self.clean_json_response(raw_response)
            extracted_json = json.loads(json_str)
            
            # Convert to ExtractedData model
            extracted_data = self.json_to_extracted_data(extracted_json)
            
            logger.info(f"✅ AI extraction successful! Confidence: {extracted_data.confidence_score}")
            return extracted_data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing error: {e}")
            logger.error(f"Raw response: {raw_response}")
            return self.create_fallback_data(raw_response)
            
        except Exception as e:
            logger.error(f"❌ AI extraction failed: {e}")
            return None
    
    def clean_json_response(self, response: str) -> str:
        """Clean AI response to extract valid JSON"""
        # Remove markdown code blocks
        response = response.replace("```json", "").replace("```", "")
        
        # Find JSON object
        start = response.find("{")
        end = response.rfind("}") + 1
        
        if start == -1 or end == 0:
            raise ValueError("No JSON object found in response")
        
        return response[start:end].strip()
    
    def json_to_extracted_data(self, data: Dict[str, Any]) -> ExtractedData:
        """Convert JSON response to ExtractedData model"""
        # Convert items
        items = []
        for item_data in data.get("items", []):
            item = ExtractedItem(
                name=item_data.get("name", "Unknown Item"),
                quantity=item_data.get("quantity", 1),
                unit_price=item_data.get("unit_price"),
                total_price=item_data.get("total_price"),
                category=item_data.get("category")
            )
            items.append(item)
        
        # Create ExtractedData
        return ExtractedData(
            merchant_name=data.get("merchant_name"),
            merchant_address=data.get("merchant_address"),
            receipt_date=data.get("receipt_date"),
            receipt_time=data.get("receipt_time"),
            receipt_number=data.get("receipt_number"),
            payment_method=data.get("payment_method"),
            currency=data.get("currency", "USD"),
            items=items,
            subtotal=data.get("subtotal"),
            tax_amount=data.get("tax_amount"),
            total_amount=data.get("total_amount"),
            confidence_score=data.get("confidence_score", 0.5),
            raw_text=data.get("raw_text", "")
        )
    
    def create_fallback_data(self, raw_response: str) -> ExtractedData:
        """Create fallback data when JSON parsing fails"""
        logger.warning("⚠️ Creating fallback extracted data")
        
        return ExtractedData(
            merchant_name="Unknown Merchant",
            merchant_address=None,
            receipt_date=None,
            receipt_time=None,
            receipt_number=None,
            payment_method=None,
            currency="USD",
            items=[],
            subtotal=None,
            tax_amount=None,
            total_amount=None,
            confidence_score=0.1,
            raw_text=raw_response[:500]  # Store partial response for debugging
        )
    
    async def process_receipt_async(self, receipt_id: str, image_url: str) -> bool:
        """Process receipt asynchronously (for background tasks)"""
        try:
            logger.info(f"🔄 Processing receipt {receipt_id} asynchronously")
            
            # Extract data
            extracted_data = await self.extract_receipt_data(image_url)
            
            if extracted_data:
                # Update receipt in database (we'll implement this in receipt_service)
                from app.services.receipt_service import ReceiptService
                from app.models.receipt import ReceiptUpdate, ReceiptStatus
                
                update_data = ReceiptUpdate(
                    extracted_data=extracted_data,
                    status=ReceiptStatus.PROCESSED
                )
                
                success = await ReceiptService.update_receipt(receipt_id, update_data)
                
                if success:
                    logger.info(f"✅ Receipt {receipt_id} processed successfully")
                    return True
                else:
                    logger.error(f"❌ Failed to update receipt {receipt_id} in database")
                    return False
            else:
                # Mark as error
                update_data = ReceiptUpdate(
                    status=ReceiptStatus.ERROR,
                    processing_error="AI extraction failed"
                )
                await ReceiptService.update_receipt(receipt_id, update_data)
                return False
                
        except Exception as e:
            logger.error(f"❌ Async processing failed for receipt {receipt_id}: {e}")
            
            # Mark as error
            from app.services.receipt_service import ReceiptService
            from app.models.receipt import ReceiptUpdate, ReceiptStatus
            
            update_data = ReceiptUpdate(
                status=ReceiptStatus.ERROR,
                processing_error=str(e)
            )
            await ReceiptService.update_receipt(receipt_id, update_data)
            return False

# Create global instance
ai_service = AIService()
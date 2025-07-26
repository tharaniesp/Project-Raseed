# app/services/document_ai_service.py
"""
Google Document AI Service for Enhanced Receipt Processing
=========================================================

This service integrates Google Document AI to provide:
1. Enhanced receipt parsing with specialized AI models
2. Better merchant detection and categorization
3. Automatic field extraction (tax, tip, discounts, line items)
4. Multi-language receipt support
5. Integration with existing agent system
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import base64
from dataclasses import dataclass

# Google Cloud imports
try:
    from google.cloud import documentai_v1 as documentai
    from google.cloud import aiplatform
    from google.api_core import exceptions as gcp_exceptions
    DOCUMENT_AI_AVAILABLE = True
except ImportError:
    DOCUMENT_AI_AVAILABLE = False
    documentai = None
    aiplatform = None
    gcp_exceptions = None

# Local imports
from app.core.config import settings
from app.models.receipt import ExtractedItem, ExtractedData
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)

@dataclass
class DocumentAIResult:
    """Structured result from Document AI processing"""
    merchant_name: str
    total_amount: float
    tax_amount: Optional[float]
    tip_amount: Optional[float]
    subtotal: Optional[float]
    date: Optional[datetime]
    items: List[ExtractedItem]
    confidence_score: float
    raw_text: str
    extracted_fields: Dict[str, Any]
    processing_time_ms: int

class DocumentAIService:
    """Service for processing receipts using Google Document AI"""
    
    def __init__(self):
        """Initialize Document AI service"""
        self.project_id = settings.FIREBASE_PROJECT_ID
        self.location = settings.DOCUMENT_AI_LOCATION or "us"
        
        # Document AI processor IDs for different receipt types
        self.processors = {
            "receipt": settings.DOCUMENT_AI_RECEIPT_PROCESSOR_ID,
            "invoice": settings.DOCUMENT_AI_INVOICE_PROCESSOR_ID,
            "form": settings.DOCUMENT_AI_FORM_PROCESSOR_ID
        }
        
        # Initialize Document AI client
        self.client = None
        if DOCUMENT_AI_AVAILABLE:
            try:
                self.client = documentai.DocumentProcessorServiceClient()
                logger.info(f"✅ Document AI client initialized for project: {self.project_id}")
            except Exception as e:
                logger.warning(f"⚠️ Document AI client initialization failed: {e}")
                self.client = None
        
        # Check if processors are configured
        self._validate_processors()
    
    def _validate_processors(self):
        """Validate that Document AI processors are configured"""
        if not self.client:
            return
            
        for processor_type, processor_id in self.processors.items():
            if processor_id:
                try:
                    processor_name = f"projects/{self.project_id}/locations/{self.location}/processors/{processor_id}"
                    self.client.get_processor(name=processor_name)
                    logger.info(f"✅ Document AI {processor_type} processor validated: {processor_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Document AI {processor_type} processor not found: {e}")
    
    def is_available(self) -> bool:
        """Check if Document AI is available and configured"""
        return (
            DOCUMENT_AI_AVAILABLE and 
            self.client is not None and 
            any(self.processors.values())
        )
    
    async def process_receipt_image(self, image_bytes: bytes, processor_type: str = "receipt") -> Optional[DocumentAIResult]:
        """Process receipt image using Document AI"""
        if not self.is_available():
            logger.warning("⚠️ Document AI not available, falling back to Gemini Vision")
            return None
        
        processor_id = self.processors.get(processor_type)
        if not processor_id:
            logger.warning(f"⚠️ No processor configured for type: {processor_type}")
            return None
        
        try:
            start_time = datetime.now()
            
            # Prepare the document
            document = documentai.Document(
                content=base64.b64encode(image_bytes).decode("utf-8"),
                mime_type="image/jpeg"
            )
            
            # Configure the process request
            processor_name = f"projects/{self.project_id}/locations/{self.location}/processors/{processor_id}"
            request = documentai.ProcessRequest(
                name=processor_name,
                document=document
            )
            
            # Process the document
            result = self.client.process_document(request=request)
            document = result.document
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Extract structured data
            extracted_data = self._extract_structured_data(document)
            
            # Create result object
            result = DocumentAIResult(
                merchant_name=extracted_data.get("merchant_name", "Unknown"),
                total_amount=extracted_data.get("total_amount", 0.0),
                tax_amount=extracted_data.get("tax_amount"),
                tip_amount=extracted_data.get("tip_amount"),
                subtotal=extracted_data.get("subtotal"),
                date=extracted_data.get("date"),
                items=extracted_data.get("items", []),
                confidence_score=extracted_data.get("confidence_score", 0.0),
                raw_text=document.text,
                extracted_fields=extracted_data,
                processing_time_ms=int(processing_time)
            )
            
            logger.info(f"✅ Document AI processed receipt in {processing_time:.0f}ms")
            return result
            
        except Exception as e:
            logger.error(f"❌ Document AI processing failed: {e}")
            return None
    
    def _extract_structured_data(self, document: documentai.Document) -> Dict[str, Any]:
        """Extract structured data from Document AI response"""
        extracted_data = {
            "merchant_name": "Unknown",
            "total_amount": 0.0,
            "tax_amount": None,
            "tip_amount": None,
            "subtotal": None,
            "date": None,
            "items": [],
            "confidence_score": 0.0
        }
        
        try:
            # Extract entities from the document
            entities = document.entities
            
            for entity in entities:
                entity_type = entity.type_
                entity_text = entity.mention_text
                confidence = entity.confidence
                
                # Update confidence score
                extracted_data["confidence_score"] = max(
                    extracted_data["confidence_score"], 
                    confidence
                )
                
                # Map entity types to our data structure
                if entity_type == "merchant_name":
                    extracted_data["merchant_name"] = entity_text
                elif entity_type == "total_amount":
                    extracted_data["total_amount"] = self._parse_amount(entity_text)
                elif entity_type == "tax_amount":
                    extracted_data["tax_amount"] = self._parse_amount(entity_text)
                elif entity_type == "tip_amount":
                    extracted_data["tip_amount"] = self._parse_amount(entity_text)
                elif entity_type == "subtotal":
                    extracted_data["subtotal"] = self._parse_amount(entity_text)
                elif entity_type == "date":
                    extracted_data["date"] = self._parse_date(entity_text)
                elif entity_type == "line_item":
                    # Extract line item details
                    item = self._extract_line_item(entity)
                    if item:
                        extracted_data["items"].append(item)
            
            # If no items found, try to extract from text
            if not extracted_data["items"]:
                extracted_data["items"] = self._extract_items_from_text(document.text)
            
            logger.info(f"📊 Extracted {len(extracted_data['items'])} items from Document AI")
            
        except Exception as e:
            logger.error(f"❌ Error extracting structured data: {e}")
        
        return extracted_data
    
    def _parse_amount(self, amount_text: str) -> Optional[float]:
        """Parse amount from text"""
        try:
            # Remove currency symbols and whitespace
            cleaned = amount_text.replace("$", "").replace(",", "").strip()
            return float(cleaned)
        except (ValueError, AttributeError):
            return None
    
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Parse date from text"""
        try:
            # Try common date formats
            formats = [
                "%m/%d/%Y",
                "%m-%d-%Y", 
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%d-%m-%Y"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_text, fmt)
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None
    
    def _extract_line_item(self, entity) -> Optional[ExtractedItem]:
        """Extract line item from Document AI entity"""
        try:
            # Get properties from the entity
            properties = {}
            for prop in entity.properties:
                properties[prop.type_] = prop.mention_text
            
            # Create receipt item
            item = ExtractedItem(
                name=properties.get("item_name", "Unknown Item"),
                quantity=float(properties.get("quantity", 1)),
                unit_price=float(properties.get("unit_price", 0)),
                total_price=float(properties.get("total_price", 0)),
                category=self._guess_category(properties.get("item_name", ""))
            )
            
            return item
        except Exception as e:
            logger.warning(f"⚠️ Error extracting line item: {e}")
            return None
    
    def _extract_items_from_text(self, text: str) -> List[ExtractedItem]:
        """Fallback: Extract items from raw text using regex patterns"""
        items = []
        
        try:
            # Simple regex patterns for common receipt formats
            import re
            
            # Pattern for items with prices
            patterns = [
                r"(\d+)\s+(.+?)\s+\$?(\d+\.?\d*)",  # "2 Milk $3.99"
                r"(.+?)\s+\$?(\d+\.?\d*)",          # "Milk $3.99"
                r"(\d+)\s+(.+?)\s+(\d+\.?\d*)",     # "2 Milk 3.99"
            ]
            
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                for pattern in patterns:
                    match = re.search(pattern, line)
                    if match:
                        groups = match.groups()
                        if len(groups) == 3:
                            # Format: quantity, name, price
                            quantity = float(groups[0])
                            name = groups[1].strip()
                            price = float(groups[2])
                        elif len(groups) == 2:
                            # Format: name, price
                            quantity = 1.0
                            name = groups[0].strip()
                            price = float(groups[1])
                        else:
                            continue
                        
                        item = ExtractedItem(
                            name=name,
                            quantity=quantity,
                            unit_price=price / quantity,
                            total_price=price,
                            category=self._guess_category(name)
                        )
                        items.append(item)
                        break
            
        except Exception as e:
            logger.warning(f"⚠️ Error extracting items from text: {e}")
        
        return items
    
    def _guess_category(self, item_name: str) -> str:
        """Guess category based on item name"""
        item_name_lower = item_name.lower()
        
        # Food categories
        if any(word in item_name_lower for word in ["milk", "cheese", "yogurt", "cream"]):
            return "dairy"
        elif any(word in item_name_lower for word in ["apple", "banana", "orange", "fruit"]):
            return "fruits"
        elif any(word in item_name_lower for word in ["bread", "pasta", "rice", "cereal"]):
            return "grains"
        elif any(word in item_name_lower for word in ["chicken", "beef", "pork", "fish", "meat"]):
            return "meat"
        elif any(word in item_name_lower for word in ["soap", "shampoo", "toothpaste"]):
            return "personal_care"
        elif any(word in item_name_lower for word in ["detergent", "cleaner", "paper"]):
            return "household"
        else:
            return "other"
    
    async def get_processing_stats(self) -> Dict[str, Any]:
        """Get Document AI processing statistics"""
        return {
            "document_ai_available": self.is_available(),
            "processors_configured": {
                processor_type: bool(processor_id) 
                for processor_type, processor_id in self.processors.items()
            },
            "project_id": self.project_id,
            "location": self.location,
            "supported_processors": list(self.processors.keys())
        }

# Global instance
document_ai_service = DocumentAIService() 
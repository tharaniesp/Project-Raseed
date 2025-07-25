# app/services/vertex_ai_agent_service.py
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import re

# Local imports (always available)
from app.core.config import settings
from app.models.receipt import (
    QueryRequest, QueryResponse, QueryType, ActionableItem, 
    ShoppingListItem, ShoppingListResponse
)
from app.services.receipt_service import ReceiptService

# Try to import optional dependencies with fallbacks
try:
    import google.generativeai as genai
    GENERATIVE_AI_AVAILABLE = True
    # Configure with API key if available
    if settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)
except ImportError:
    GENERATIVE_AI_AVAILABLE = False
    genai = None

try:
    from google.cloud import aiplatform
    from google.cloud import discoveryengine_v1 as discoveryengine
    from google.api_core import exceptions as gcp_exceptions
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    discoveryengine = None
    aiplatform = None
    gcp_exceptions = None

try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    
try:
    from googletrans import Translator
    GOOGLETRANS_AVAILABLE = True
except ImportError:
    GOOGLETRANS_AVAILABLE = False

logger = logging.getLogger(__name__)

class VertexAIAgentService:
    """Service for handling local language queries using AI models"""
    
    def __init__(self):
        """Initialize AI Agent Service"""
        self.project_id = settings.FIREBASE_PROJECT_ID
        self.location = settings.VERTEX_AI_LOCATION
        
        # Initialize based on configuration
        self.use_vertex_ai = settings.USE_VERTEX_AI and VERTEX_AI_AVAILABLE
        self.use_generative_ai = settings.USE_GENERATIVE_AI and GENERATIVE_AI_AVAILABLE
        
        # Set up translator if available
        self.translator = None
        if GOOGLETRANS_AVAILABLE:
            try:
                self.translator = Translator()
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize translator: {e}")
        
        # Initialize Vertex AI if enabled and available
        if self.use_vertex_ai:
            try:
                import vertexai
                vertexai.init(project=self.project_id, location=self.location)
                logger.info(f"✅ Vertex AI initialized: {self.project_id} in {self.location}")
            except Exception as e:
                logger.warning(f"⚠️ Vertex AI initialization failed: {e}")
                self.use_vertex_ai = False
        
        # Log which AI service will be used
        if self.use_generative_ai:
            logger.info(f"✅ Using Google Generative AI with model: {settings.GENERATIVE_AI_MODEL}")
        elif self.use_vertex_ai:
            logger.info(f"✅ Using Vertex AI with model: {settings.VERTEX_AI_MODEL}")
        else:
            logger.warning("⚠️ No AI service available - queries will return fallback responses")

    def is_available(self) -> bool:
        """Check if any AI service is available"""
        return self.use_generative_ai or self.use_vertex_ai
    
    def detect_language(self, text: str) -> str:
        """Detect language of input text"""
        if not LANGDETECT_AVAILABLE:
            logger.warning("⚠️ langdetect not available, defaulting to 'en'")
            return 'en'
            
        try:
            detected = detect(text)
            logger.info(f"🌐 Detected language: {detected}")
            return detected
        except Exception as e:
            logger.warning(f"⚠️ Language detection failed: {e}, defaulting to 'en'")
            return 'en'
    
    async def translate_to_english(self, text: str, source_lang: str) -> str:
        """Translate text to English for processing"""
        if source_lang == 'en':
            return text
        
        if not GOOGLETRANS_AVAILABLE or not self.translator:
            logger.warning("⚠️ googletrans not available, returning original text")
            return text
        
        try:
            translated = await self.translator.translate(text, src=source_lang, dest='en')
            logger.info(f"🔄 Translated '{text[:50]}...' from {source_lang} to English")
            return translated.text
        except Exception as e:
            logger.error(f"❌ Translation failed: {e}")
            return text
    
    async def translate_from_english(self, text: str, target_lang: str) -> str:
        """Translate response back to user's language"""
        if target_lang == 'en':
            return text
        
        if not GOOGLETRANS_AVAILABLE or not self.translator:
            logger.warning("⚠️ googletrans not available, returning English text")
            return text
        
        try:
            translated = await self.translator.translate(text, src='en', dest=target_lang)
            logger.info(f"🔄 Translated response back to {target_lang}")
            return translated.text
        except Exception as e:
            logger.error(f"❌ Response translation failed: {e}")
            return text
    
    def classify_query_type(self, query: str) -> QueryType:
        """Classify the type of query to determine response strategy"""
        query_lower = query.lower()
        
        # Cooking and recipe related
        cooking_keywords = ['cook', 'recipe', 'make', 'prepare', 'dish', 'meal', 'ingredient', 'kitchen']
        if any(keyword in query_lower for keyword in cooking_keywords):
            return QueryType.COOKING_SUGGESTIONS
        
        # Shopping list related
        shopping_keywords = ['buy', 'need', 'shopping', 'list', 'purchase', 'get', 'missing']
        if any(keyword in query_lower for keyword in shopping_keywords):
            return QueryType.SHOPPING_LIST
        
        # Inventory check
        inventory_keywords = ['have', 'enough', 'do i have', 'check', 'inventory', 'stock']
        if any(keyword in query_lower for keyword in inventory_keywords):
            return QueryType.INVENTORY_CHECK
        
        # Spending analysis
        spending_keywords = ['spent', 'cost', 'money', 'budget', 'expensive', 'cheap', 'price']
        if any(keyword in query_lower for keyword in spending_keywords):
            return QueryType.SPENDING_ANALYSIS
        
        return QueryType.GENERAL
    
    async def get_user_receipt_data(self, user_id: Optional[str], days_back: int = 14) -> List[Dict]:
        """Get user's recent receipt data for context"""
        try:
            # Get recent receipts (last 2 weeks by default)
            receipts = await ReceiptService.get_receipts(limit=50, offset=0)
            
            # Filter processed receipts with extracted data
            relevant_receipts = []
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            for receipt in receipts:
                if (receipt.extracted_data and 
                    receipt.created_at >= cutoff_date):
                    
                    receipt_data = {
                        'date': receipt.extracted_data.receipt_date or receipt.created_at.strftime('%Y-%m-%d'),
                        'merchant': receipt.extracted_data.merchant_name,
                        'total': receipt.extracted_data.total_amount,
                        'items': []
                    }
                    
                    for item in receipt.extracted_data.items:
                        receipt_data['items'].append({
                            'name': item.name,
                            'quantity': item.quantity,
                            'category': item.category,
                            'price': item.total_price
                        })
                    
                    relevant_receipts.append(receipt_data)
            
            logger.info(f"📊 Retrieved {len(relevant_receipts)} recent receipts for analysis")
            return relevant_receipts
            
        except Exception as e:
            logger.error(f"❌ Failed to get receipt data: {e}")
            return []
    
    def create_context_prompt(self, query: str, receipts_data: List[Dict], query_type: QueryType) -> str:
        """Create context-aware prompt for the AI agent"""
        
        # Create a summary of available items
        all_items = []
        for receipt in receipts_data:
            all_items.extend(receipt.get('items', []))
        
        # Group items by category
        categories = {}
        for item in all_items:
            category = item.get('category', 'other').lower()
            if category not in categories:
                categories[category] = []
            categories[category].append(item['name'])
        
        context = f"""
        You are a helpful shopping and cooking assistant. The user has the following items from their recent purchases (last 2 weeks):

        AVAILABLE ITEMS BY CATEGORY:
        {json.dumps(categories, indent=2)}

        RECENT RECEIPTS:
        {json.dumps(receipts_data[-5:], indent=2)}  # Last 5 receipts for context

        USER QUERY: {query}
        QUERY TYPE: {query_type.value}

        Instructions based on query type:
        
        {self._get_type_specific_instructions(query_type)}

        RESPONSE FORMAT:
        - Provide a helpful, natural response
        - If suggesting shopping items, format as: "SHOPPING_LIST: item1, item2, item3"
        - If providing cooking suggestions, be specific about recipes
        - Always be practical and consider what the user already has
        """
        
        return context
    
    def _get_type_specific_instructions(self, query_type: QueryType) -> str:
        """Get specific instructions based on query type"""
        if query_type == QueryType.COOKING_SUGGESTIONS:
            return """
            - Suggest recipes based on items they already have
            - Mention what additional ingredients they might need
            - Provide step-by-step cooking instructions
            - Consider dietary restrictions if mentioned
            """
        elif query_type == QueryType.SHOPPING_LIST:
            return """
            - Create a shopping list based on their request
            - Consider what they already have to avoid duplicates
            - Suggest quantities where appropriate
            - Group items by store section if possible
            - Format shopping items clearly with SHOPPING_LIST: prefix
            """
        elif query_type == QueryType.INVENTORY_CHECK:
            return """
            - Check if they have the items they're asking about
            - Be specific about quantities if possible
            - Suggest alternatives if they don't have something
            """
        elif query_type == QueryType.SPENDING_ANALYSIS:
            return """
            - Analyze their spending patterns
            - Provide insights about costs and budgeting
            - Suggest ways to save money
            """
        else:
            return """
            - Provide helpful information based on their purchase history
            - Be conversational and helpful
            """
    
    async def process_query_with_ai(self, context_prompt: str) -> str:
        """Process query using available AI service"""
        if self.use_generative_ai and GENERATIVE_AI_AVAILABLE:
            return await self.process_query_with_generative_ai(context_prompt)
        elif self.use_vertex_ai and VERTEX_AI_AVAILABLE:
            return await self.process_query_with_vertex_ai(context_prompt)
        else:
            logger.warning("⚠️ No AI service available, returning fallback response")
            return "I apologize, but I'm currently unable to process your request due to AI service limitations. Please try again later."

    async def process_query_with_generative_ai(self, context_prompt: str) -> str:
        """Process query using Google Generative AI"""
        try:
            logger.info("🤖 Processing with Google Generative AI...")
            
            model = genai.GenerativeModel(settings.GENERATIVE_AI_MODEL)
            
            generation_config = genai.types.GenerationConfig(
                temperature=0.7,
                top_p=0.8,
                top_k=40,
                max_output_tokens=2048,
            )
            
            response = model.generate_content(
                context_prompt,
                generation_config=generation_config
            )
            
            if response.text:
                logger.info("✅ Google Generative AI response received")
                return response.text
            else:
                logger.warning("⚠️ Empty response from Google Generative AI")
                return "I couldn't generate a response. Please try rephrasing your question."
                
        except Exception as e:
            logger.error(f"❌ Google Generative AI error: {e}")
            return f"I encountered an error processing your request: {str(e)}"

    async def process_query_with_vertex_ai(self, context_prompt: str) -> str:
        """Process query using Vertex AI (fallback method)"""
        try:
            logger.info("🤖 Processing with Vertex AI...")
            
            from vertexai.generative_models import GenerativeModel
            model = GenerativeModel(settings.VERTEX_AI_MODEL)
            
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
            
            response = model.generate_content(
                context_prompt,
                generation_config=generation_config
            )
            
            if response.text:
                logger.info("✅ Vertex AI response received")
                return response.text
            else:
                logger.warning("⚠️ Empty response from Vertex AI")
                return "I couldn't generate a response. Please try rephrasing your question."
                
        except Exception as e:
            logger.error(f"❌ Vertex AI error: {e}")
            return f"I encountered an error with Vertex AI: {str(e)}"
    
    def extract_actionable_items(self, response_text: str, query_type: QueryType) -> List[ActionableItem]:
        """Extract actionable items (shopping list items) from AI response"""
        actionable_items = []
        
        # Look for shopping list format in ANY response, not just SHOPPING_LIST type
        shopping_pattern = r'SHOPPING_LIST:\s*(.+?)(?:\n|$)'
        match = re.search(shopping_pattern, response_text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        
        if match:
            items_text = match.group(1)
            # Split by comma, removing extra whitespace and parenthetical notes
            items = [item.strip() for item in items_text.split(',')]
            
            for item in items:
                if item:
                    # Clean up the item text (remove parenthetical notes)
                    clean_item = re.sub(r'\s*\([^)]*\)', '', item).strip()
                    
                    # Simple quantity extraction
                    quantity_match = re.match(r'(\d+)\s*(.+)', clean_item)
                    if quantity_match:
                        quantity = quantity_match.group(1)
                        name = quantity_match.group(2).strip()
                    else:
                        quantity = "1"
                        name = clean_item
                    
                    # Skip empty names or very short names
                    if name and len(name) > 2:
                        actionable_items.append(ActionableItem(
                            name=name,
                            quantity=quantity,
                            category=self._guess_category(name),
                            priority="normal"
                        ))
        
        logger.info(f"🛒 Extracted {len(actionable_items)} actionable items from response")
        return actionable_items
    
    def _guess_category(self, item_name: str) -> str:
        """Guess category for an item"""
        item_lower = item_name.lower()
        
        food_keywords = ['bread', 'milk', 'eggs', 'cheese', 'fruit', 'vegetable', 'meat', 'rice', 'pasta']
        household_keywords = ['detergent', 'soap', 'paper', 'cleaner', 'shampoo', 'toothpaste']
        
        if any(keyword in item_lower for keyword in food_keywords):
            return "food"
        elif any(keyword in item_lower for keyword in household_keywords):
            return "household"
        else:
            return "other"
    
    async def process_query(self, request: QueryRequest) -> QueryResponse:
        """Main method to process a natural language query using available AI service"""
        try:
            logger.info(f"🔍 Processing query: {request.query[:100]}...")
            
            # Detect language
            detected_language = request.language or self.detect_language(request.query)
            logger.info(f"🌐 Detected language: {detected_language}")
            
            # Translate to English if needed for processing
            english_query = await self.translate_to_english(request.query, detected_language)
            
            # Classify query type
            query_type = self.classify_query_type(english_query)
            logger.info(f"📊 Classified as: {query_type.value}")
            
            # Get user's receipt data for context
            receipts_data = await self.get_user_receipt_data(request.user_id)
            logger.info(f"📊 Retrieved {len(receipts_data)} recent receipts")
            
            # Create context prompt
            context_prompt = await self.create_enhanced_context_prompt(english_query, receipts_data, query_type)
            
            # Process with available AI service
            ai_response = await self.process_query_with_ai(context_prompt)
            
            # Extract actionable items
            actionable_items = self.extract_actionable_items(ai_response, query_type)
            logger.info(f"🛒 Extracted {len(actionable_items)} actionable items")
            
            # Update query type if shopping items were found
            if actionable_items and query_type != QueryType.SHOPPING_LIST:
                query_type = QueryType.SHOPPING_LIST
                logger.info(f"🛒 Updated query type to shopping_list due to actionable items")
            
            # Translate response back to user's language
            translated_response = await self.translate_from_english(ai_response, detected_language)
            
            # Determine if we can create a wallet pass
            can_create_wallet_pass = len(actionable_items) > 0
            
            # Generate suggested actions
            suggested_actions = []
            if can_create_wallet_pass:
                suggested_actions.append("Create Google Wallet pass with shopping list")
            if query_type == QueryType.COOKING_SUGGESTIONS:
                suggested_actions.append("Save recipe for later")
            
            # Calculate confidence score
            confidence = 0.8 if self.is_available() else 0.5
            
            return QueryResponse(
                answer=translated_response,
                confidence=confidence,
                query_type=query_type,
                detected_language=detected_language,
                sources=[f"AI Service: {'Google Generative AI' if self.use_generative_ai else 'Vertex AI' if self.use_vertex_ai else 'Fallback'}"],
                actionable_items=actionable_items,
                can_create_wallet_pass=can_create_wallet_pass,
                suggested_actions=suggested_actions
            )
            
        except Exception as e:
            logger.error(f"❌ Query processing failed: {e}")
            return QueryResponse(
                answer="I apologize, but I encountered an error processing your request. Please try again.",
                confidence=0.0,
                query_type=QueryType.GENERAL,
                detected_language=request.language or 'en',
                sources=[],
                actionable_items=[],
                can_create_wallet_pass=False,
                suggested_actions=["Try rephrasing your question", "Contact support if issue persists"]
            )
    
    def _get_suggested_actions(self, query_type: QueryType, actionable_items: List[ActionableItem]) -> List[str]:
        """Get suggested actions based on query type and results"""
        actions = []
        
        if query_type == QueryType.SHOPPING_LIST and actionable_items:
            actions.append("Create Google Wallet pass with shopping list")
            actions.append("Set shopping reminders")
        elif query_type == QueryType.COOKING_SUGGESTIONS:
            actions.append("Save favorite recipes")
            actions.append("Create shopping list for missing ingredients")
        elif query_type == QueryType.SPENDING_ANALYSIS:
            actions.append("Set budget alerts")
            actions.append("View detailed spending report")
        
        return actions

    async def create_enhanced_context_prompt(self, query: str, receipts_data: List[Dict], query_type: QueryType) -> str:
        """Create enhanced context prompt specifically for Vertex AI Agent"""
        
        # Create a structured data context for Vertex AI
        context_data = {
            "user_query": query,
            "query_type": query_type.value,
            "available_items": [],
            "recent_purchases": [],
            "dietary_preferences": [],
            "budget_constraints": []
        }
        
        # Extract available items with better categorization
        for receipt in receipts_data:
            purchase_info = {
                "date": receipt.get('date'),
                "merchant": receipt.get('merchant'),
                "total": receipt.get('total'),
                "items": receipt.get('items', [])
            }
            context_data["recent_purchases"].append(purchase_info)
            
            # Add items to available items list
            for item in receipt.get('items', []):
                if item.get('name'):
                    context_data["available_items"].append({
                        "name": item.get('name'),
                        "category": item.get('category', 'other'),
                        "quantity": item.get('quantity'),
                        "purchase_date": receipt.get('date')
                    })
        
        # Create Vertex AI optimized prompt
        prompt = f"""
Role: You are an intelligent shopping and cooking assistant with access to the user's purchase history.

User Query: {query}
Query Type: {query_type.value}

Available Ingredients and Items:
{json.dumps(context_data["available_items"], indent=2)}

Recent Purchase History:
{json.dumps(context_data["recent_purchases"], indent=2)}

Instructions based on query type:
{self._get_vertex_ai_instructions(query_type)}

Response Requirements:
1. Provide a helpful, natural response in the same language as the user's query
2. If suggesting items to purchase, format them as: "SHOPPING_LIST: item1, item2, item3"
3. Be specific and practical
4. Consider what the user already has to avoid duplicates
5. For cooking queries, provide step-by-step instructions
6. For shopping queries, organize items by category when possible

Context: The user has made {len(receipts_data)} purchases in the last 2 weeks totaling {len(context_data['available_items'])} items.
"""
        
        return prompt
    
    def _get_vertex_ai_instructions(self, query_type: QueryType) -> str:
        """Get Vertex AI specific instructions for different query types"""
        instructions = {
            QueryType.COOKING_SUGGESTIONS: """
- Analyze available ingredients and suggest complete recipes
- Mention cooking techniques and estimated cooking time
- Identify missing ingredients and suggest where to buy them
- Provide difficulty level and serving suggestions
- Include nutritional benefits when relevant
""",
            QueryType.SHOPPING_LIST: """
- Create comprehensive shopping lists based on the request
- Organize items by store sections (produce, dairy, pantry, etc.)
- Suggest quantities based on typical usage
- Consider seasonal availability and pricing
- Format as "SHOPPING_LIST: item1, item2, item3" for wallet pass generation
""",
            QueryType.INVENTORY_CHECK: """
- Check available quantities against user needs
- Estimate how long current supplies will last
- Suggest optimal restock timing
- Recommend storage tips to extend freshness
- Alert to potential shortages
""",
            QueryType.SPENDING_ANALYSIS: """
- Analyze spending patterns and trends
- Identify opportunities for savings
- Compare prices across different merchants
- Suggest budget-friendly alternatives
- Provide spending category breakdowns
""",
            QueryType.GENERAL: """
- Provide helpful information based on purchase history
- Suggest related products or services
- Offer general cooking and shopping tips
- Be conversational and helpful
"""
        }
        
        return instructions.get(query_type, instructions[QueryType.GENERAL])

# Create global instance with error handling
try:
    vertex_ai_agent_service = VertexAIAgentService()
except Exception as e:
    logger.error(f"❌ Failed to initialize VertexAIAgentService: {e}")
    vertex_ai_agent_service = None 
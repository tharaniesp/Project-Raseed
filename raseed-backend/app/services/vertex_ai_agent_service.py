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
        """Detect language of input text with enhanced Indian language support"""
        if not LANGDETECT_AVAILABLE:
            logger.warning("⚠️ langdetect not available, defaulting to 'en'")
            return 'en'
            
        try:
            detected = detect(text)
            logger.info(f"🌐 Detected language: {detected}")
            
            # Map some common Indian languages that langdetect might not catch properly
            indian_language_keywords = {
                'hi': ['हिंदी', 'मैं', 'क्या', 'कैसे', 'कहाँ', 'कौन', 'कब', 'में', 'से', 'पर', 'को', 'का', 'की', 'के'],
                'ta': ['தமிழ்', 'என்', 'எது', 'எப்படி', 'எங்கே', 'யார்', 'எப்போது', 'இல்', 'இருந்து', 'மேல்', 'க்கு', 'ன்', 'ள்', 'ம்'],
                'kn': ['ಕನ್ನಡ', 'ನಾನು', 'ಏನು', 'ಹೇಗೆ', 'ಎಲ್ಲಿ', 'ಯಾರು', 'ಯಾವಾಗ', 'ಲಿ', 'ಇಂದ', 'ಮೇಲೆ', 'ಗೆ', 'ನ್ನ', 'ಳ್ಳ', 'ಮ್ಮ'],
                'te': ['తెలుగు', 'నేను', 'ఏమి', 'ఎలా', 'ఎక్కడ', 'ఎవరు', 'ఎప్పుడు', 'లో', 'నుండి', 'మీద', 'కు', 'న్న', 'ల్ల', 'మ్మ'],
                'ml': ['മലയാളം', 'ഞാൻ', 'എന്ത്', 'എങ്ങനെ', 'എവിടെ', 'ആര്', 'എപ്പോൾ', 'ൽ', 'നിന്ന്', 'മേൽ', 'ക്ക്', 'ന്ന', 'ള്ള', 'മ്മ'],
                'gu': ['ગુજરાતી', 'હું', 'શું', 'કેવી', 'ક્યાં', 'કોણ', 'ક્યારે', 'માં', 'થી', 'પર', 'ને', 'ના', 'ની', 'નું'],
                'mr': ['मराठी', 'मी', 'काय', 'कसे', 'कुठे', 'कोण', 'केव्हा', 'मध्ये', 'पासून', 'वर', 'ला', 'चा', 'ची', 'चे'],
                'bn': ['বাংলা', 'আমি', 'কি', 'কিভাবে', 'কোথায়', 'কে', 'কখন', 'তে', 'থেকে', 'উপর', 'কে', 'র', 'দের', 'গুলো'],
                'pa': ['ਪੰਜਾਬੀ', 'ਮੈਂ', 'ਕੀ', 'ਕਿਵੇਂ', 'ਕਿੱਥੇ', 'ਕੌਣ', 'ਕਦੋਂ', 'ਵਿੱਚ', 'ਤੋਂ', 'ਉੱਤੇ', 'ਨੂੰ', 'ਦਾ', 'ਦੀ', 'ਦੇ']
            }
            
            # Check if any Indian language keywords are present
            for lang_code, keywords in indian_language_keywords.items():
                if any(keyword in text for keyword in keywords):
                    logger.info(f"🇮🇳 Detected Indian language by keyword matching: {lang_code}")
                    return lang_code
            
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
        """Classify the type of query to determine response strategy with Indian language support"""
        query_lower = query.lower()
        
        # Enhanced keyword sets including common Indian language terms
        # Cooking and recipe related (including Indian terms)
        cooking_keywords = [
            'cook', 'recipe', 'make', 'prepare', 'dish', 'meal', 'ingredient', 'kitchen',
            'बनाना', 'पकाना', 'खाना', 'रसोई',  # Hindi
            'சமைக்க', 'உணவு', 'அடுப்பங்கரை',  # Tamil
            'ಬೇಯಿಸು', 'ಅಡುಗೆ', 'ಆಹಾರ',  # Kannada
            'వండటం', 'వంటకాలు', 'ఆహారం',  # Telugu
            'പാചകം', 'ഭക്ഷണം', 'അടുക്കള',  # Malayalam
        ]
        if any(keyword in query_lower for keyword in cooking_keywords):
            return QueryType.COOKING_SUGGESTIONS
        
        # Shopping list related (including Indian terms)
        shopping_keywords = [
            'buy', 'need', 'shopping', 'list', 'purchase', 'get', 'missing',
            'खरीदना', 'चाहिए', 'सामान', 'लिस्ट',  # Hindi
            'வாங்க', 'தேவை', 'பட்டியல்', 'சாமான்',  # Tamil
            'ಖರೀದಿಸು', 'ಬೇಕು', 'ಪಟ್ಟಿ', 'ಸಾಮಾನು',  # Kannada
            'కొనుగోలు', 'కావాలి', 'జాబితా', 'సామాను',  # Telugu
            'വാങ്ങുക', 'വേണം', 'പട്ടിക', 'സാധനം',  # Malayalam
        ]
        if any(keyword in query_lower for keyword in shopping_keywords):
            return QueryType.SHOPPING_LIST
        
        # Inventory check (including Indian terms)
        inventory_keywords = [
            'have', 'enough', 'do i have', 'check', 'inventory', 'stock',
            'है', 'पास', 'जांच', 'स्टॉक',  # Hindi
            'இருக்கிறது', 'போதும்', 'பார்க்க', 'கையிருப்பு',  # Tamil
            'ಇದೆ', 'ಸಾಕು', 'ನೋಡು', 'ಸ್ಟಾಕ್',  # Kannada
            'ఉంది', 'చాలు', 'చూడు', 'స్టాక్',  # Telugu
            'ഉണ്ട്', 'മതി', 'നോക്കു', 'സ്റ്റോക്ക്',  # Malayalam
        ]
        if any(keyword in query_lower for keyword in inventory_keywords):
            return QueryType.INVENTORY_CHECK
        
        # Spending analysis (including Indian terms)
        spending_keywords = [
            'spent', 'cost', 'money', 'budget', 'expensive', 'cheap', 'price',
            'खर्च', 'पैसा', 'दाम', 'बजट', 'महंगा', 'सस्ता',  # Hindi
            'செலவு', 'பணம்', 'விலை', 'பட்ஜெட்', 'விலை உயர்ந்த', 'மலிவான',  # Tamil
            'ಖರ್ಚು', 'ಹಣ', 'ಬೆಲೆ', 'ಬಜೆಟ್', 'ದುಬಾರಿ', 'ಅಗ್ಗ',  # Kannada
            'ఖర్చు', 'డబ్బు', 'ధర', 'బడ్జెట్', 'ఖరీదైన', 'చౌక',  # Telugu
            'ചിലവ്', 'പണം', 'വില', 'ബഡ്ജറ്റ്', 'ചെലവേറിയ', 'വിലകുറഞ്ഞ',  # Malayalam
        ]
        if any(keyword in query_lower for keyword in spending_keywords):
            return QueryType.SPENDING_ANALYSIS
        
        return QueryType.GENERAL
    
    async def get_user_receipt_data(self, user_id: Optional[str], days_back: int = 14) -> List[Dict]:
        """Get user's recent receipt data for context from Firestore"""
        try:
            # Use insights service to get real receipt data from Firestore
            from app.services.insights_service import insights_service
            
            # Get real receipt data from Firestore
            receipts_data = await insights_service._get_user_receipts(user_id or "current_user", days_back)
            
            # Transform the data to match expected format
            relevant_receipts = []
            
            for receipt in receipts_data:
                receipt_data = {
                    'receipt_id': receipt.get('receipt_id', ''),
                    'date': receipt.get('date', datetime.now()).strftime('%Y-%m-%d') if hasattr(receipt.get('date'), 'strftime') else str(receipt.get('date', datetime.now())),
                    'merchant': receipt.get('merchant', 'Unknown Merchant'),
                    'category': receipt.get('category', 'general'),
                    'total': receipt.get('total', receipt.get('amount', 0.0)),
                    'items': []
                }
                
                # Handle different item formats
                items = receipt.get('items', [])
                parsed_items = receipt.get('parsed_items', [])
                
                if parsed_items:
                    # Use parsed items if available
                    for item in parsed_items:
                        if isinstance(item, dict):
                            receipt_data['items'].append({
                                'name': item.get('name', 'Unknown Item'),
                                'quantity': item.get('quantity', '1'),
                                'category': item.get('category', 'other'),
                                'price': item.get('price', 0.0)
                            })
                elif items:
                    # Use simple items list
                    for item in items:
                        if isinstance(item, str):
                            receipt_data['items'].append({
                                'name': item,
                                'quantity': '1',
                                'category': 'other',
                                'price': 0.0
                            })
                        elif isinstance(item, dict):
                            receipt_data['items'].append({
                                'name': item.get('name', 'Unknown Item'),
                                'quantity': item.get('quantity', '1'),
                                'category': item.get('category', 'other'),
                                'price': item.get('price', 0.0)
                            })
                
                relevant_receipts.append(receipt_data)
            
            logger.info(f"📊 Retrieved {len(relevant_receipts)} real receipts from Firestore for analysis")
            return relevant_receipts
            
        except Exception as e:
            logger.error(f"❌ Failed to get receipt data from Firestore: {e}")
            # Fallback to empty list
            return []
    
    def create_context_prompt(self, query: str, receipts_data: List[Dict], query_type: QueryType) -> str:
        """Create context-aware prompt for the AI agent with real receipt data"""
        
        if not receipts_data:
            return f"""
            You are a helpful shopping and cooking assistant. The user has no recent receipt data available.

            USER QUERY: {query}
            QUERY TYPE: {query_type.value}

            Instructions based on query type:
            {self._get_type_specific_instructions(query_type)}

            RESPONSE FORMAT:
            - Provide a helpful, natural response
            - If suggesting shopping items, format as: "SHOPPING_LIST: item1, item2, item3"
            - If providing cooking suggestions, be specific about recipes
            - Since no receipt data is available, provide general advice
            """
        
        # Create a comprehensive summary of available items and spending patterns
        all_items = []
        merchant_spending = {}
        category_spending = {}
        total_spending = 0
        
        for receipt in receipts_data:
            merchant = receipt.get('merchant', 'Unknown')
            category = receipt.get('category', 'general')
            total = receipt.get('total', 0)
            
            # Track spending by merchant and category
            merchant_spending[merchant] = merchant_spending.get(merchant, 0) + total
            category_spending[category] = category_spending.get(category, 0) + total
            total_spending += total
            
            # Collect all items
            all_items.extend(receipt.get('items', []))
        
        # Group items by category
        categories = {}
        for item in all_items:
            category = item.get('category', 'other').lower()
            if category not in categories:
                categories[category] = []
            categories[category].append(item['name'])
        
        # Create spending summary
        spending_summary = f"""
        SPENDING SUMMARY (Last {len(receipts_data)} receipts):
        - Total Spent: ₹{total_spending:.2f}
        - Top Merchants: {', '.join([f"{m} (₹{amt:.0f})" for m, amt in sorted(merchant_spending.items(), key=lambda x: x[1], reverse=True)[:3]])}
        - Top Categories: {', '.join([f"{c} (₹{amt:.0f})" for c, amt in sorted(category_spending.items(), key=lambda x: x[1], reverse=True)[:3]])}
        """
        
        # Create detailed receipt summary
        receipt_summary = "RECENT RECEIPTS:\n"
        for i, receipt in enumerate(receipts_data[-5:], 1):  # Last 5 receipts
            receipt_summary += f"""
            Receipt {i}:
            - Date: {receipt.get('date', 'Unknown')}
            - Merchant: {receipt.get('merchant', 'Unknown')}
            - Category: {receipt.get('category', 'general')}
            - Total: ₹{receipt.get('total', 0):.2f}
            - Items: {', '.join([item.get('name', 'Unknown') for item in receipt.get('items', [])[:5]])}
            """
        
        context = f"""
        You are a helpful shopping and cooking assistant with access to the user's real receipt data from their recent purchases.

        {spending_summary}

        AVAILABLE ITEMS BY CATEGORY:
        {json.dumps(categories, indent=2)}

        {receipt_summary}

        USER QUERY: {query}
        QUERY TYPE: {query_type.value}

        Instructions based on query type:
        {self._get_type_specific_instructions(query_type)}

        IMPORTANT CONTEXT:
        - Use the actual receipt data to provide personalized responses
        - Consider their spending patterns and preferences
        - Reference specific merchants they frequently visit
        - Suggest items based on what they typically buy
        - Consider their budget based on their spending history

        RESPONSE FORMAT:
        - Provide a helpful, natural response based on their actual data
        - If suggesting shopping items, format as: "SHOPPING_LIST: item1, item2, item3"
        - If providing cooking suggestions, be specific about recipes using their available items
        - Always be practical and consider what the user already has
        - Reference their spending patterns when relevant
        """
        
        return context
    
    def _get_type_specific_instructions(self, query_type: QueryType) -> str:
        """Get specific instructions based on query type with enhanced Indian language support"""
        if query_type == QueryType.COOKING_SUGGESTIONS:
            return """
            - Suggest recipes based on items they already have, with preference for Indian cuisine if detected
            - Mention what additional Indian spices or ingredients they might need
            - Provide step-by-step cooking instructions in the user's language
            - Include traditional Indian cooking techniques (tempering, slow cooking, etc.)
            - Consider dietary restrictions and regional preferences if mentioned
            - Use both English and local names for ingredients when helpful
            """
        elif query_type == QueryType.SHOPPING_LIST:
            return """
            - Create a shopping list based on their request in their preferred language
            - For Indian users, include common Indian grocery items and spices
            - Consider what they already have to avoid duplicates
            - Suggest quantities appropriate for Indian household sizes
            - Group items by store section (vegetables, grains, spices, dairy, etc.)
            - Include both English and local names for better clarity
            - Format shopping items clearly with SHOPPING_LIST: prefix
            """
        elif query_type == QueryType.INVENTORY_CHECK:
            return """
            - Check if they have the items they're asking about
            - For Indian pantry items, consider typical storage and usage patterns
            - Be specific about quantities if possible
            - Suggest alternatives if they don't have something, preferring Indian substitutes
            - Include traditional Indian storage tips
            """
        elif query_type == QueryType.SPENDING_ANALYSIS:
            return """
            - Analyze their spending patterns with cultural context
            - For Indian users, compare with typical Indian household spending
            - Be specific about costs and budgeting in local currency (₹)
            - Suggest ways to save money using Indian shopping wisdom
            - Consider seasonal variations in Indian markets
            """
        else:
            return """
            - Provide helpful information based on their purchase history
            - Be conversational and helpful in their preferred language
            - Include culturally relevant suggestions for Indian users
            - Reference traditional cooking and shopping wisdom
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
        """Process query using Google Generative AI with enhanced Indian language support"""
        try:
            logger.info("🤖 Processing with Google Generative AI (with Indian language support)...")
            
            model = genai.GenerativeModel(settings.GENERATIVE_AI_MODEL)
            
            # Enhanced generation config for better multilingual support
            generation_config = genai.types.GenerationConfig(
                temperature=0.7,  # Balanced creativity for natural responses
                top_p=0.8,       # Good diversity while maintaining quality
                top_k=40,        # Reasonable token selection
                max_output_tokens=2048,  # Sufficient for detailed responses in any language
                candidate_count=1
            )
            
            # Add system instruction for better Indian language handling
            enhanced_prompt = f"""
You are a helpful AI assistant specializing in Indian household management, cooking, and shopping. 
You understand and can respond fluently in multiple Indian languages including Hindi, Tamil, Kannada, Telugu, Malayalam, Gujarati, Marathi, Bengali, and Punjabi.

CRITICAL: Always respond in the SAME LANGUAGE as the user's query. Maintain the original script and cultural context.

{context_prompt}

Additional Guidelines for Indian Language Responses:
- Use appropriate honorifics and polite forms
- Include traditional Indian cooking wisdom
- Reference common Indian ingredients and spices
- Consider regional cooking variations
- Use metric measurements (kg, grams, liters)
- Include cultural context in suggestions
"""
            
            response = model.generate_content(
                enhanced_prompt,
                generation_config=generation_config
            )
            
            if response.text:
                logger.info("✅ Google Generative AI response received (with Indian language support)")
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
            receipts_data = []
            
            # Check if receipt data is provided from frontend context
            if request.context and request.context.get('use_frontend_receipts') and request.context.get('receipts_data'):
                logger.info(f"📊 Using receipt data from frontend context: {len(request.context['receipts_data'])} receipts")
                receipts_data = request.context['receipts_data']
            else:
                # Fallback to fetching from Firestore
                receipts_data = await self.get_user_receipt_data(request.user_id)
                logger.info(f"📊 Retrieved {len(receipts_data)} recent receipts from Firestore")
            
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
        
        # Create Vertex AI optimized prompt with enhanced multi-language support
        prompt = f"""
Role: You are an intelligent shopping and cooking assistant with access to the user's purchase history. You are capable of understanding and responding in multiple languages including Indian languages like Hindi, Tamil, Kannada, Telugu, Malayalam, Gujarati, Marathi, Bengali, and Punjabi.

User Query: {query}
Query Type: {query_type.value}

Available Ingredients and Items:
{json.dumps(context_data["available_items"], indent=2)}

Recent Purchase History:
{json.dumps(context_data["recent_purchases"], indent=2)}

Instructions based on query type:
{self._get_vertex_ai_instructions(query_type)}

Response Requirements:
1. **IMPORTANT**: Respond in the SAME LANGUAGE as the user's query. If the user asks in Hindi, respond in Hindi. If in Tamil, respond in Tamil, etc.
2. For Indian languages, use appropriate script (Devanagari for Hindi, Tamil script for Tamil, etc.)
3. If suggesting items to purchase, format them as: "SHOPPING_LIST: item1, item2, item3" (this part can remain in English for technical processing)
4. Be specific and practical, considering Indian cooking preferences and ingredients
5. Consider what the user already has to avoid duplicates
6. For cooking queries, provide step-by-step instructions in the user's language
7. For shopping queries, organize items by category when possible
8. Use culturally appropriate references and cooking methods for Indian users
9. Include both English and local names for ingredients when helpful (e.g., "हल्दी (turmeric)")

Special Instructions for Indian Language Responses:
- Use polite forms appropriate to the language
- Reference common Indian spices, ingredients, and cooking methods
- Consider regional preferences (e.g., rice-based dishes for South India, wheat-based for North India)
- Use appropriate measurement units (kg, grams, liters)
- Include traditional cooking tips where relevant

Context: The user has made {len(receipts_data)} purchases in the last 2 weeks totaling {len(context_data['available_items'])} items.
"""
        
        return prompt
    
    def _get_vertex_ai_instructions(self, query_type: QueryType) -> str:
        """Get Vertex AI specific instructions for different query types with Indian language support"""
        instructions = {
            QueryType.COOKING_SUGGESTIONS: """
- Analyze available ingredients and suggest complete recipes in the user's language
- For Indian language queries, suggest traditional Indian recipes and cooking methods
- Include both ingredient names in English and local language where helpful
- Mention cooking techniques specific to Indian cuisine (tadka, dum cooking, etc.)
- Provide estimated cooking time and difficulty level
- Identify missing ingredients and suggest where to buy them
- Include nutritional benefits when relevant
- Consider regional cooking preferences (South Indian vs North Indian styles)
""",
            QueryType.SHOPPING_LIST: """
- Create comprehensive shopping lists in the user's language
- For Indian users, include common Indian grocery items and spices
- Organize items by store sections (vegetables, grains, spices, dairy, etc.)
- Suggest quantities based on typical Indian household usage
- Consider seasonal availability and local pricing
- Include both English and local names for items
- Format as "SHOPPING_LIST: item1, item2, item3" for wallet pass generation
- Suggest visiting specific types of stores (local sabzi mandi, grocery stores, etc.)
""",
            QueryType.INVENTORY_CHECK: """
- Check available quantities against user needs in their preferred language
- For Indian pantry items, consider typical storage and shelf life
- Estimate how long current supplies will last based on Indian cooking patterns
- Suggest optimal restock timing for perishables vs non-perishables
- Recommend traditional Indian storage tips to extend freshness
- Alert to potential shortages of essential Indian cooking ingredients (rice, lentils, spices)
""",
            QueryType.SPENDING_ANALYSIS: """
- Analyze spending patterns and provide insights in the user's language
- For Indian users, compare prices with typical Indian market rates
- Identify opportunities for savings (bulk buying of rice/lentils, seasonal vegetables)
- Compare prices across different types of stores (supermarkets vs local vendors)
- Suggest budget-friendly Indian alternatives and substitutes
- Provide spending category breakdowns relevant to Indian households
- Consider festival seasons and their impact on grocery spending
""",
            QueryType.GENERAL: """
- Provide helpful information in the user's preferred language
- For Indian users, include culturally relevant suggestions
- Reference traditional Indian cooking wisdom and tips
- Suggest related Indian products or seasonal items
- Offer general cooking and shopping tips relevant to Indian households
- Be conversational and respectful of cultural preferences
"""
        }
        
        return instructions.get(query_type, instructions[QueryType.GENERAL])

# Create global instance with error handling
try:
    vertex_ai_agent_service = VertexAIAgentService()
except Exception as e:
    logger.error(f"❌ Failed to initialize VertexAIAgentService: {e}")
    vertex_ai_agent_service = None 
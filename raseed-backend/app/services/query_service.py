# app/services/query_service.py
import logging
from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime

from app.models.receipt import (
    QueryRequest, QueryResponse, QueryType, ActionableItem,
    WalletPassRequest, WalletPassResponse, ShoppingListResponse, ShoppingListItem
)
from app.services.vertex_ai_agent_service import vertex_ai_agent_service
from app.services.wallet_service import WalletService

logger = logging.getLogger(__name__)

class QueryService:
    """Main service for handling natural language queries and actions"""
    
    def __init__(self):
        """Initialize QueryService"""
        self.query_cache = {}  # Simple in-memory cache for recent queries
        self.max_cache_size = 100
    
    async def process_natural_language_query(self, request: QueryRequest) -> QueryResponse:
        """Process a natural language query and return structured response"""
        try:
            logger.info(f"🔍 Processing natural language query: {request.query[:100]}...")
            
            # Generate unique query ID for tracking
            query_id = str(uuid.uuid4())
            
            # Add query ID to request context
            if not request.context:
                request.context = {}
            request.context['query_id'] = query_id
            
            # Check if receipt data is provided in context from frontend
            if request.context and request.context.get('receipts_data'):
                logger.info(f"📊 Using receipt data from frontend context: {len(request.context['receipts_data'])} receipts")
                # Pass the receipt data to the agent service
                request.context['use_frontend_receipts'] = True
            
            # Process with Vertex AI Agent
            response = await vertex_ai_agent_service.process_query(request)
            
            # Cache the response for potential wallet pass generation
            self._cache_query_response(query_id, request, response)
            
            # Add query ID to response for wallet pass generation
            if response.can_create_wallet_pass:
                response.suggested_actions.insert(0, f"Create wallet pass (Query ID: {query_id})")
            
            logger.info(f"✅ Query processed successfully. Type: {response.query_type}, "
                       f"Actionable items: {len(response.actionable_items)}")
            
            return response
            
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
    
    async def create_wallet_pass_from_query(self, request: WalletPassRequest) -> WalletPassResponse:
        """Create a Google Wallet pass from a previous query response"""
        try:
            logger.info(f"🎫 Creating wallet pass for query: {request.query_id}")
            
            # Get cached query response
            cached_data = self._get_cached_query(request.query_id)
            if not cached_data:
                return WalletPassResponse(
                    success=False,
                    error="Query not found or expired. Please submit a new query.",
                    items_count=0
                )
            
            query_response = cached_data['response']
            
            # Use custom items if provided, otherwise use items from query response
            items_to_use = request.custom_items or query_response.actionable_items
            
            if not items_to_use:
                return WalletPassResponse(
                    success=False,
                    error="No actionable items found to create wallet pass.",
                    items_count=0
                )
            
            # Check if wallet service is available
            if not WalletService.is_wallet_available():
                return WalletPassResponse(
                    success=False,
                    error="Google Wallet service is not configured. Please check system settings.",
                    items_count=0
                )
            
            # Create pass title
            pass_title = request.pass_title or self._generate_pass_title(query_response.query_type, items_to_use)
            
            # Convert ActionableItems to format expected by WalletService
            wallet_items = []
            total_estimated_cost = 0.0
            
            for item in items_to_use:
                wallet_item = {
                    'name': item.name,
                    'quantity': item.quantity or "1",
                    'category': item.category or "other",
                    'priority': item.priority or "normal"
                }
                
                if item.estimated_price:
                    wallet_item['estimated_price'] = item.estimated_price
                    total_estimated_cost += item.estimated_price
                
                wallet_items.append(wallet_item)
            
            # Create the wallet pass
            result = await WalletService.create_shopping_list_pass(
                title=pass_title,
                items=wallet_items,
                estimated_total=total_estimated_cost if total_estimated_cost > 0 else None,
                metadata={
                    'query_id': request.query_id,
                    'query_type': query_response.query_type.value,
                    'detected_language': query_response.detected_language,
                    'creation_date': datetime.now().isoformat()
                }
            )
            
            # Clean up cache entry after successful wallet pass creation
            self._remove_cached_query(request.query_id)
            
            logger.info(f"✅ Wallet pass created successfully: {result['object_id']}")
            
            return WalletPassResponse(
                success=True,
                wallet_object_id=result['object_id'],
                save_url=result['save_url'],
                class_id=result.get('class_id'),
                items_count=len(wallet_items)
            )
            
        except Exception as e:
            logger.error(f"❌ Wallet pass creation failed: {e}")
            return WalletPassResponse(
                success=False,
                error=f"Failed to create wallet pass: {str(e)}",
                items_count=0
            )
    
    async def generate_shopping_list(self, query: str, user_id: Optional[str] = None) -> ShoppingListResponse:
        """Generate a detailed shopping list based on a query"""
        try:
            logger.info(f"🛒 Generating shopping list for query: {query[:50]}...")
            
            # Create query request
            request = QueryRequest(
                query=query,
                user_id=user_id,
                context={'purpose': 'shopping_list_generation'}
            )
            
            # Process the query
            response = await vertex_ai_agent_service.process_query(request)
            
            # Convert actionable items to shopping list items
            shopping_items = []
            total_estimated_cost = 0.0
            suggested_stores = set()
            
            for item in response.actionable_items:
                shopping_item = ShoppingListItem(
                    name=item.name,
                    quantity=item.quantity or "1",
                    category=item.category or "other",
                    estimated_price=item.estimated_price,
                    priority=item.priority or "normal",
                    suggested_store=self._suggest_store_for_category(item.category),
                    notes=None
                )
                
                shopping_items.append(shopping_item)
                
                if item.estimated_price:
                    total_estimated_cost += item.estimated_price
                
                if shopping_item.suggested_store:
                    suggested_stores.add(shopping_item.suggested_store)
            
            # Generate title based on query type
            title = self._generate_shopping_list_title(response.query_type, len(shopping_items))
            
            return ShoppingListResponse(
                title=title,
                items=shopping_items,
                total_estimated_cost=total_estimated_cost if total_estimated_cost > 0 else None,
                suggested_stores=list(suggested_stores),
                budget_friendly_alternatives=self._get_budget_alternatives(shopping_items)
            )
            
        except Exception as e:
            logger.error(f"❌ Shopping list generation failed: {e}")
            return ShoppingListResponse(
                title="Shopping List",
                items=[],
                total_estimated_cost=None,
                suggested_stores=[],
                budget_friendly_alternatives=[]
            )
    
    def _cache_query_response(self, query_id: str, request: QueryRequest, response: QueryResponse):
        """Cache query response for potential wallet pass generation"""
        # Clean up cache if it's getting too large
        if len(self.query_cache) >= self.max_cache_size:
            # Remove oldest entries (simple FIFO)
            oldest_key = next(iter(self.query_cache))
            del self.query_cache[oldest_key]
        
        self.query_cache[query_id] = {
            'request': request,
            'response': response,
            'timestamp': datetime.now(),
            'used': False
        }
        
        logger.debug(f"📦 Cached query response: {query_id}")
    
    def _get_cached_query(self, query_id: str) -> Optional[Dict[str, Any]]:
        """Get cached query response"""
        cached_data = self.query_cache.get(query_id)
        
        if cached_data:
            # Check if cache entry is not too old (1 hour expiry)
            age = datetime.now() - cached_data['timestamp']
            if age.total_seconds() > 3600:  # 1 hour
                del self.query_cache[query_id]
                return None
            
            # Mark as used
            cached_data['used'] = True
            return cached_data
        
        return None
    
    def _remove_cached_query(self, query_id: str):
        """Remove query from cache"""
        if query_id in self.query_cache:
            del self.query_cache[query_id]
            logger.debug(f"🗑️ Removed cached query: {query_id}")
    
    def _generate_pass_title(self, query_type: QueryType, items: list) -> str:
        """Generate appropriate title for wallet pass"""
        item_count = len(items)
        
        if query_type == QueryType.SHOPPING_LIST:
            return f"Shopping List ({item_count} items)"
        elif query_type == QueryType.COOKING_SUGGESTIONS:
            return f"Recipe Ingredients ({item_count} items)"
        else:
            return f"Shopping List ({item_count} items)"
    
    def _generate_shopping_list_title(self, query_type: QueryType, item_count: int) -> str:
        """Generate title for shopping list"""
        if query_type == QueryType.COOKING_SUGGESTIONS:
            return f"Recipe Shopping List ({item_count} ingredients)"
        elif query_type == QueryType.SHOPPING_LIST:
            return f"Shopping List ({item_count} items)"
        else:
            return f"Generated Shopping List ({item_count} items)"
    
    def _suggest_store_for_category(self, category: Optional[str]) -> Optional[str]:
        """Suggest appropriate store based on item category"""
        if not category:
            return None
        
        category_lower = category.lower()
        
        if category_lower in ['food', 'groceries', 'produce', 'dairy', 'meat']:
            return "Grocery Store"
        elif category_lower in ['household', 'cleaning', 'personal care']:
            return "Supermarket"
        elif category_lower in ['electronics', 'tech']:
            return "Electronics Store"
        elif category_lower in ['pharmacy', 'health', 'medicine']:
            return "Pharmacy"
        else:
            return "General Store"
    
    def _get_budget_alternatives(self, items: List[ShoppingListItem]) -> List[str]:
        """Get budget-friendly alternatives suggestions"""
        alternatives = []
        
        high_cost_categories = set()
        for item in items:
            if item.estimated_price and item.estimated_price > 10:  # Arbitrary threshold
                high_cost_categories.add(item.category)
        
        if 'food' in high_cost_categories:
            alternatives.append("Consider store brands for basic food items")
            alternatives.append("Look for seasonal produce for better prices")
        
        if 'household' in high_cost_categories:
            alternatives.append("Buy household items in bulk for savings")
            alternatives.append("Check for generic cleaning product alternatives")
        
        if len(items) > 10:
            alternatives.append("Consider splitting shopping across multiple trips")
        
        return alternatives[:3]  # Return top 3 suggestions
    
    def get_query_statistics(self) -> Dict[str, Any]:
        """Get statistics about recent queries"""
        total_queries = len(self.query_cache)
        used_queries = sum(1 for data in self.query_cache.values() if data['used'])
        
        # Count by query type
        type_counts = {}
        for data in self.query_cache.values():
            query_type = data['response'].query_type.value
            type_counts[query_type] = type_counts.get(query_type, 0) + 1
        
        return {
            'total_cached_queries': total_queries,
            'used_for_wallet_passes': used_queries,
            'query_types': type_counts,
            'cache_utilization': f"{(used_queries/total_queries*100):.1f}%" if total_queries > 0 else "0%"
        }

# Create global instance
query_service = QueryService()

# app/services/agent_orchestration_service.py
"""
Agent Orchestration Service for Multi-Agent Coordination
=======================================================

This service orchestrates multiple specialized agents:
1. Receipt Analysis Agent - Processes and categorizes receipts
2. Budget Management Agent - Tracks spending and budget limits
3. Shopping List Agent - Generates and manages shopping lists
4. Notification Agent - Handles alerts and notifications
5. Insights Agent - Generates spending insights and trends

This demonstrates advanced agent coordination for the hackathon.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import asyncio
import json
from dataclasses import dataclass
from enum import Enum

# Local imports
from app.core.config import settings
from app.models.receipt import QueryRequest, QueryResponse, QueryType, ActionableItem, ExtractedItem
from app.services.vertex_ai_agent_service import vertex_ai_agent_service
from app.services.document_ai_service import document_ai_service
from app.services.insights_service import insights_service
from app.services.wallet_service import WalletService
from app.services.notification_service import notification_service
from app.services.receipt_service import ReceiptService

logger = logging.getLogger(__name__)

class AgentType(Enum):
    """Types of specialized agents"""
    RECEIPT_ANALYSIS = "receipt_analysis"
    BUDGET_MANAGEMENT = "budget_management"
    SHOPPING_LIST = "shopping_list"
    NOTIFICATION = "notification"
    INSIGHTS = "insights"
    WALLET = "wallet"

@dataclass
class AgentTask:
    """Represents a task for a specific agent"""
    agent_type: AgentType
    task_id: str
    priority: int
    description: str
    input_data: Dict[str, Any]
    created_at: datetime
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@dataclass
class AgentResult:
    """Result from agent execution"""
    agent_type: AgentType
    success: bool
    data: Dict[str, Any]
    confidence: float
    processing_time_ms: int
    metadata: Dict[str, Any]

class AgentOrchestrationService:
    """Service for orchestrating multiple specialized agents"""
    
    def __init__(self):
        """Initialize agent orchestration service"""
        self.agents = {}
        self.task_queue = []
        self.results_cache = {}
        self.agent_stats = {}
        
        # Initialize specialized agents
        self._initialize_agents()
        
        logger.info("✅ Agent orchestration service initialized")
    
    def _initialize_agents(self):
        """Initialize all specialized agents"""
        # Receipt Analysis Agent
        self.agents[AgentType.RECEIPT_ANALYSIS] = {
            "name": "Receipt Analysis Agent",
            "description": "Processes and categorizes receipts using Document AI",
            "capabilities": ["receipt_parsing", "merchant_detection", "item_categorization"],
            "available": True  # Always available, can use mock data
        }
        
        # Budget Management Agent
        self.agents[AgentType.BUDGET_MANAGEMENT] = {
            "name": "Budget Management Agent", 
            "description": "Tracks spending and manages budget limits",
            "capabilities": ["spending_tracking", "budget_alerts", "overspending_detection"],
            "available": True
        }
        
        # Shopping List Agent
        self.agents[AgentType.SHOPPING_LIST] = {
            "name": "Shopping List Agent",
            "description": "Generates and manages shopping lists",
            "capabilities": ["list_generation", "item_suggestions", "budget_optimization"],
            "available": True
        }
        
        # Notification Agent
        self.agents[AgentType.NOTIFICATION] = {
            "name": "Notification Agent",
            "description": "Handles alerts and notifications",
            "capabilities": ["alert_generation", "notification_routing", "priority_management"],
            "available": True
        }
        
        # Insights Agent
        self.agents[AgentType.INSIGHTS] = {
            "name": "Insights Agent",
            "description": "Generates spending insights and trends",
            "capabilities": ["trend_analysis", "insight_generation", "pattern_recognition"],
            "available": True
        }
        
        # Wallet Agent
        self.agents[AgentType.WALLET] = {
            "name": "Wallet Agent",
            "description": "Manages Google Wallet integration",
            "capabilities": ["pass_generation", "wallet_integration", "digital_cards"],
            "available": True
        }
    
    async def process_complex_query(self, request: QueryRequest) -> QueryResponse:
        """Process complex queries using multiple agents"""
        try:
            logger.info(f"🤖 Orchestrating agents for query: {request.query[:100]}...")
            
            # Create orchestration task
            task_id = f"orchestration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Step 1: Route query to appropriate agents
            agent_tasks = await self._route_query_to_agents(request)
            
            # Step 2: Execute tasks in parallel
            results = await self._execute_agent_tasks(agent_tasks)
            
            # Step 3: Synthesize results
            final_response = await self._synthesize_results(request, results)
            
            # Step 4: Trigger follow-up actions
            await self._trigger_follow_up_actions(final_response, results)
            
            logger.info(f"✅ Agent orchestration completed for task {task_id}")
            return final_response
            
        except Exception as e:
            logger.error(f"❌ Agent orchestration failed: {e}")
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
    
    async def _route_query_to_agents(self, request: QueryRequest) -> List[AgentTask]:
        """Route query to appropriate agents based on content"""
        tasks = []
        query_lower = request.query.lower()
        
        # Always include insights agent for context
        tasks.append(AgentTask(
            agent_type=AgentType.INSIGHTS,
            task_id=f"insights_{datetime.now().strftime('%H%M%S')}",
            priority=1,
            description="Generate spending insights for context",
            input_data={"query": request.query, "user_id": request.user_id},
            created_at=datetime.now()
        ))
        
        # Route based on query content
        if any(word in query_lower for word in ["receipt", "bill", "purchase", "bought"]):
            tasks.append(AgentTask(
                agent_type=AgentType.RECEIPT_ANALYSIS,
                task_id=f"receipt_{datetime.now().strftime('%H%M%S')}",
                priority=2,
                description="Analyze receipt data",
                input_data={"query": request.query, "user_id": request.user_id},
                created_at=datetime.now()
            ))
        
        if any(word in query_lower for word in ["budget", "spending", "money", "cost", "expensive"]):
            tasks.append(AgentTask(
                agent_type=AgentType.BUDGET_MANAGEMENT,
                task_id=f"budget_{datetime.now().strftime('%H%M%S')}",
                priority=2,
                description="Analyze budget and spending patterns",
                input_data={"query": request.query, "user_id": request.user_id},
                created_at=datetime.now()
            ))
        
        if any(word in query_lower for word in ["shopping", "list", "buy", "need", "ingredients"]):
            tasks.append(AgentTask(
                agent_type=AgentType.SHOPPING_LIST,
                task_id=f"shopping_{datetime.now().strftime('%H%M%S')}",
                priority=2,
                description="Generate shopping list",
                input_data={"query": request.query, "user_id": request.user_id},
                created_at=datetime.now()
            ))
        
        # Add notification agent for actionable queries
        if any(word in query_lower for word in ["alert", "notify", "remind", "warn"]):
            tasks.append(AgentTask(
                agent_type=AgentType.NOTIFICATION,
                task_id=f"notification_{datetime.now().strftime('%H%M%S')}",
                priority=3,
                description="Setup notifications",
                input_data={"query": request.query, "user_id": request.user_id},
                created_at=datetime.now()
            ))
        
        return tasks
    
    async def _execute_agent_tasks(self, tasks: List[AgentTask]) -> Dict[AgentType, AgentResult]:
        """Execute agent tasks in parallel"""
        results = {}
        
        # Create tasks for parallel execution
        async def execute_task(task: AgentTask) -> Tuple[AgentType, AgentResult]:
            start_time = datetime.now()
            
            try:
                if task.agent_type == AgentType.RECEIPT_ANALYSIS:
                    result = await self._execute_receipt_analysis_agent(task)
                elif task.agent_type == AgentType.BUDGET_MANAGEMENT:
                    result = await self._execute_budget_management_agent(task)
                elif task.agent_type == AgentType.SHOPPING_LIST:
                    result = await self._execute_shopping_list_agent(task)
                elif task.agent_type == AgentType.NOTIFICATION:
                    result = await self._execute_notification_agent(task)
                elif task.agent_type == AgentType.INSIGHTS:
                    result = await self._execute_insights_agent(task)
                elif task.agent_type == AgentType.WALLET:
                    result = await self._execute_wallet_agent(task)
                else:
                    result = AgentResult(
                        agent_type=task.agent_type,
                        success=False,
                        data={},
                        confidence=0.0,
                        processing_time_ms=0,
                        metadata={"error": "Unknown agent type"}
                    )
                
                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                result.processing_time_ms = int(processing_time)
                
                return task.agent_type, result
                
            except Exception as e:
                logger.error(f"❌ Agent task execution failed: {e}")
                return task.agent_type, AgentResult(
                    agent_type=task.agent_type,
                    success=False,
                    data={},
                    confidence=0.0,
                    processing_time_ms=0,
                    metadata={"error": str(e)}
                )
        
        # Execute all tasks in parallel
        task_coroutines = [execute_task(task) for task in tasks]
        task_results = await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        # Process results
        for result in task_results:
            if isinstance(result, Exception):
                logger.error(f"❌ Task execution exception: {result}")
                continue
            
            agent_type, agent_result = result
            results[agent_type] = agent_result
        
        return results
    
    async def _execute_receipt_analysis_agent(self, task: AgentTask) -> AgentResult:
        """Execute receipt analysis agent using real Firestore data"""
        try:
            # Get user's real receipt data from Firestore
            from app.services.insights_service import insights_service
            
            user_id = task.input_data.get('user_id', 'current_user')
            receipts_data = await insights_service._get_user_receipts(user_id, days_back=90)
            
            # Analyze receipt patterns from real data
            total_spent = sum(receipt.get('total', receipt.get('amount', 0)) for receipt in receipts_data)
            merchant_counts = {}
            category_totals = {}
            item_frequency = {}
            spending_timeline = {}
            
            for receipt in receipts_data:
                merchant = receipt.get('merchant', 'Unknown')
                category = receipt.get('category', 'general')
                total = receipt.get('total', receipt.get('amount', 0))
                date = receipt.get('date', datetime.now())
                
                # Track merchant frequency
                merchant_counts[merchant] = merchant_counts.get(merchant, 0) + 1
                
                # Track category spending
                category_totals[category] = category_totals.get(category, 0) + total
                
                # Track item frequency
                items = receipt.get('items', [])
                parsed_items = receipt.get('parsed_items', [])
                
                if parsed_items:
                    for item in parsed_items:
                        if isinstance(item, dict):
                            item_name = item.get('name', 'Unknown')
                            item_frequency[item_name] = item_frequency.get(item_name, 0) + 1
                elif items:
                    for item in items:
                        if isinstance(item, str):
                            item_frequency[item] = item_frequency.get(item, 0) + 1
                        elif isinstance(item, dict):
                            item_name = item.get('name', 'Unknown')
                            item_frequency[item_name] = item_frequency.get(item_name, 0) + 1
                
                # Track spending timeline
                if hasattr(date, 'strftime'):
                    month_key = date.strftime('%Y-%m')
                else:
                    month_key = str(date)[:7]  # Extract YYYY-MM
                spending_timeline[month_key] = spending_timeline.get(month_key, 0) + total
            
            # Find top items and merchants
            top_items = sorted(item_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
            top_merchants = sorted(merchant_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            top_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Calculate spending insights
            avg_receipt_value = total_spent / len(receipts_data) if receipts_data else 0
            most_expensive_receipt = max(receipts_data, key=lambda x: x.get('total', 0)) if receipts_data else None
            
            return AgentResult(
                agent_type=AgentType.RECEIPT_ANALYSIS,
                success=True,
                data={
                    "total_receipts": len(receipts_data),
                    "total_spent": total_spent,
                    "avg_receipt_value": avg_receipt_value,
                    "merchant_counts": dict(top_merchants),
                    "category_totals": dict(top_categories),
                    "top_items": dict(top_items),
                    "spending_timeline": spending_timeline,
                    "most_expensive_receipt": {
                        "merchant": most_expensive_receipt.get('merchant', 'Unknown'),
                        "total": most_expensive_receipt.get('total', 0),
                        "date": most_expensive_receipt.get('date', 'Unknown')
                    } if most_expensive_receipt else None,
                    "recent_receipts": receipts_data[-5:],  # Last 5 receipts
                    "analysis_period": "90 days"
                },
                confidence=0.90,
                processing_time_ms=0,
                metadata={
                    "receipts_analyzed": len(receipts_data),
                    "data_source": "Firestore",
                    "user_id": user_id
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Receipt analysis agent failed: {e}")
            return AgentResult(
                agent_type=AgentType.RECEIPT_ANALYSIS,
                success=False,
                data={},
                confidence=0.0,
                processing_time_ms=0,
                metadata={"error": str(e)}
            )
    
    async def _execute_budget_management_agent(self, task: AgentTask) -> AgentResult:
        """Execute budget management agent using real Firestore data"""
        try:
            # Get user's real receipt data and insights
            from app.services.insights_service import insights_service
            
            user_id = task.input_data.get('user_id', 'current_user')
            receipts_data = await insights_service._get_user_receipts(user_id, days_back=90)
            insights = await insights_service.get_insights(user_id)
            
            # Calculate real spending patterns
            total_spending = sum(receipt.get('total', receipt.get('amount', 0)) for receipt in receipts_data)
            monthly_spending = total_spending / 3  # Assuming 90 days = 3 months
            
            # Analyze spending by category
            category_spending = {}
            for receipt in receipts_data:
                category = receipt.get('category', 'general')
                total = receipt.get('total', receipt.get('amount', 0))
                category_spending[category] = category_spending.get(category, 0) + total
            
            # Find overspending categories (spending > 30% of total)
            overspending_categories = []
            for category, amount in category_spending.items():
                if amount > total_spending * 0.3:
                    overspending_categories.append({
                        "category": category,
                        "amount": amount,
                        "percentage": (amount / total_spending) * 100
                    })
            
            # Get overspending alerts from insights
            overspending_alerts = [
                insight for insight in insights 
                if insight.get('insight_type') == 'overspending'
            ]
            
            # Generate budget recommendations based on real data
            budget_recommendations = []
            
            if monthly_spending > 10000:  # High spending threshold
                budget_recommendations.append("Consider setting up spending limits for high-cost categories")
            
            if overspending_categories:
                budget_recommendations.append(f"Focus on reducing spending in: {', '.join([cat['category'] for cat in overspending_categories[:3]])}")
            
            if len(receipts_data) > 50:  # High frequency of purchases
                budget_recommendations.append("Consider consolidating purchases to reduce transaction frequency")
            
            # Find potential savings opportunities
            savings_opportunities = []
            for insight in insights:
                if insight.get('insight_type') == 'savings_opportunity':
                    savings_opportunities.append(insight)
            
            return AgentResult(
                agent_type=AgentType.BUDGET_MANAGEMENT,
                success=True,
                data={
                    "monthly_spending": monthly_spending,
                    "total_spending_90_days": total_spending,
                    "category_spending": category_spending,
                    "overspending_categories": overspending_categories,
                    "overspending_alerts": overspending_alerts,
                    "budget_recommendations": budget_recommendations,
                    "savings_opportunities": savings_opportunities,
                    "insights_count": len(insights),
                    "receipts_analyzed": len(receipts_data),
                    "analysis_period": "90 days"
                },
                confidence=0.85,
                processing_time_ms=0,
                metadata={
                    "data_source": "Firestore",
                    "user_id": user_id,
                    "insights_analyzed": len(insights)
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Budget management agent failed: {e}")
            return AgentResult(
                agent_type=AgentType.BUDGET_MANAGEMENT,
                success=False,
                data={},
                confidence=0.0,
                processing_time_ms=0,
                metadata={"error": str(e)}
            )
    
    async def _execute_shopping_list_agent(self, task: AgentTask) -> AgentResult:
        """Execute shopping list agent"""
        try:
            # Use existing query service for shopping list generation
            from app.services.query_service import QueryService
            query_service = QueryService()
            
            shopping_list = await query_service.generate_shopping_list(
                task.input_data.get('query', ''),
                task.input_data.get('user_id')
            )
            
            return AgentResult(
                agent_type=AgentType.SHOPPING_LIST,
                success=True,
                data={
                    "shopping_list": shopping_list.dict() if hasattr(shopping_list, 'dict') else shopping_list,
                    "items_count": len(shopping_list.items) if hasattr(shopping_list, 'items') else 0
                },
                confidence=0.90,
                processing_time_ms=0,
                metadata={"list_generated": True}
            )
            
        except Exception as e:
            logger.error(f"❌ Shopping list agent failed: {e}")
            return AgentResult(
                agent_type=AgentType.SHOPPING_LIST,
                success=False,
                data={},
                confidence=0.0,
                processing_time_ms=0,
                metadata={"error": str(e)}
            )
    
    async def _execute_notification_agent(self, task: AgentTask) -> AgentResult:
        """Execute notification agent"""
        try:
            # Analyze query for notification triggers
            query = task.input_data.get('query', '').lower()
            notification_triggers = []
            
            if "budget" in query and "alert" in query:
                notification_triggers.append("budget_alert")
            if "spending" in query and "limit" in query:
                notification_triggers.append("spending_limit")
            if "remind" in query:
                notification_triggers.append("reminder")
            
            return AgentResult(
                agent_type=AgentType.NOTIFICATION,
                success=True,
                data={
                    "notification_triggers": notification_triggers,
                    "user_id": task.input_data.get('user_id'),
                    "query_analysis": "Notification setup requested"
                },
                confidence=0.75,
                processing_time_ms=0,
                metadata={"triggers_found": len(notification_triggers)}
            )
            
        except Exception as e:
            logger.error(f"❌ Notification agent failed: {e}")
            return AgentResult(
                agent_type=AgentType.NOTIFICATION,
                success=False,
                data={},
                confidence=0.0,
                processing_time_ms=0,
                metadata={"error": str(e)}
            )
    
    async def _execute_insights_agent(self, task: AgentTask) -> AgentResult:
        """Execute insights agent"""
        try:
            # Get comprehensive insights
            insights = await insights_service.get_insights(task.input_data.get('user_id', 'current_user'))
            trends = await insights_service.get_spending_trends(task.input_data.get('user_id', 'current_user'))
            
            return AgentResult(
                agent_type=AgentType.INSIGHTS,
                success=True,
                data={
                    "insights": insights,
                    "trends": trends,
                    "insights_count": len(insights)
                },
                confidence=0.85,
                processing_time_ms=0,
                metadata={"insights_generated": len(insights)}
            )
            
        except Exception as e:
            logger.error(f"❌ Insights agent failed: {e}")
            return AgentResult(
                agent_type=AgentType.INSIGHTS,
                success=False,
                data={},
                confidence=0.0,
                processing_time_ms=0,
                metadata={"error": str(e)}
            )
    
    async def _execute_wallet_agent(self, task: AgentTask) -> AgentResult:
        """Execute wallet agent"""
        try:
            # Check wallet service availability
            wallet_available = WalletService.is_wallet_available()
            
            return AgentResult(
                agent_type=AgentType.WALLET,
                success=wallet_available,
                data={
                    "wallet_available": wallet_available,
                    "issuer_id": WalletService.get_issuer_id() if wallet_available else None
                },
                confidence=1.0 if wallet_available else 0.0,
                processing_time_ms=0,
                metadata={"service_status": "available" if wallet_available else "unavailable"}
            )
            
        except Exception as e:
            logger.error(f"❌ Wallet agent failed: {e}")
            return AgentResult(
                agent_type=AgentType.WALLET,
                success=False,
                data={},
                confidence=0.0,
                processing_time_ms=0,
                metadata={"error": str(e)}
            )
    
    async def _synthesize_results(self, request: QueryRequest, results: Dict[AgentType, AgentResult]) -> QueryResponse:
        """Synthesize results from multiple agents into a coherent response"""
        try:
            # Use Vertex AI to synthesize results
            context_prompt = self._build_synthesis_prompt(request, results)
            
            # Get AI response with timeout
            try:
                ai_response = await asyncio.wait_for(
                    vertex_ai_agent_service.process_query_with_ai(context_prompt),
                    timeout=10.0
                )
            except asyncio.TimeoutError:
                logger.warning("⚠️ AI synthesis timeout, using fallback response")
                ai_response = "I analyzed your request using multiple agents. Here's what I found based on your data."
            except Exception as ai_error:
                logger.error(f"❌ AI synthesis failed: {ai_error}")
                ai_response = "I processed your request using multiple AI agents. Here's what I found based on your data."
            
            # Extract actionable items safely
            actionable_items = []
            for agent_type, result in results.items():
                if result.success and result.data:
                    if agent_type == AgentType.SHOPPING_LIST and 'shopping_list' in result.data:
                        shopping_list = result.data['shopping_list']
                        # Handle different shopping list formats
                        if isinstance(shopping_list, dict) and 'items' in shopping_list:
                            # If it's a dict with items key
                            items = shopping_list['items']
                            if isinstance(items, list):
                                actionable_items.extend(items)
                        elif hasattr(shopping_list, 'items') and callable(getattr(shopping_list, 'items', None)):
                            # If it's an object with items method
                            try:
                                actionable_items.extend(shopping_list.items)
                            except Exception:
                                pass
                        elif isinstance(shopping_list, list):
                            # If it's directly a list of items
                            actionable_items.extend(shopping_list)
            
            # Determine if wallet pass can be created
            can_create_wallet = (
                results.get(AgentType.WALLET, AgentResult(AgentType.WALLET, False, {}, 0.0, 0, {})).success and
                actionable_items
            )
            
            return QueryResponse(
                answer=ai_response,
                confidence=0.90,  # High confidence due to multi-agent validation
                query_type=QueryType.GENERAL,
                detected_language=request.language or 'en',
                sources=[f"Multi-agent analysis ({len(results)} agents)"],
                actionable_items=actionable_items,
                can_create_wallet_pass=can_create_wallet,
                suggested_actions=[
                    "View detailed insights",
                    "Create shopping list wallet pass" if actionable_items else "No actionable items",
                    "Set up budget alerts"
                ]
            )
            
        except Exception as e:
            logger.error(f"❌ Result synthesis failed: {e}")
            return QueryResponse(
                answer="I processed your request using multiple AI agents but encountered an error synthesizing the results.",
                confidence=0.5,
                query_type=QueryType.GENERAL,
                detected_language=request.language or 'en',
                sources=[],
                actionable_items=[],
                can_create_wallet_pass=False,
                suggested_actions=["Try rephrasing your question"]
            )
    
    def _build_synthesis_prompt(self, request: QueryRequest, results: Dict[AgentType, AgentResult]) -> str:
        """Build prompt for synthesizing agent results"""
        prompt = f"""
        User Query: {request.query}
        
        Agent Results:
        """
        
        for agent_type, result in results.items():
            if result.success:
                prompt += f"\n{agent_type.value.upper()} AGENT:\n"
                prompt += f"- Data: {json.dumps(result.data, indent=2)}\n"
                prompt += f"- Confidence: {result.confidence}\n"
            else:
                prompt += f"\n{agent_type.value.upper()} AGENT: Failed - {result.metadata.get('error', 'Unknown error')}\n"
        
        prompt += """
        
        Please synthesize these results into a comprehensive, helpful response that:
        1. Directly answers the user's query
        2. Incorporates insights from all successful agents
        3. Provides actionable recommendations
        4. Maintains a conversational tone
        5. Highlights the most important findings
        
        Response:
        """
        
        return prompt
    
    async def _trigger_follow_up_actions(self, response: QueryResponse, results: Dict[AgentType, AgentResult]):
        """Trigger follow-up actions based on agent results"""
        try:
            # Send notifications if notification agent was involved
            if AgentType.NOTIFICATION in results:
                notification_result = results[AgentType.NOTIFICATION]
                if notification_result.success and notification_result.data.get('notification_triggers'):
                    await notification_service.send_notification(
                        user_id=notification_result.data.get('user_id', 'current_user'),
                        title="Agent Analysis Complete",
                        message=f"Your query has been analyzed by {len(results)} AI agents. Check the results for insights and recommendations.",
                        notification_type="agent_analysis"
                    )
            
            # Update agent statistics
            for agent_type, result in results.items():
                if agent_type not in self.agent_stats:
                    self.agent_stats[agent_type] = {"executions": 0, "successes": 0, "total_time": 0}
                
                self.agent_stats[agent_type]["executions"] += 1
                if result.success:
                    self.agent_stats[agent_type]["successes"] += 1
                self.agent_stats[agent_type]["total_time"] += result.processing_time_ms
            
        except Exception as e:
            logger.error(f"❌ Follow-up actions failed: {e}")
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {
            "agents": {
                agent_type.value: {
                    "name": agent_info["name"],
                    "description": agent_info["description"],
                    "capabilities": agent_info["capabilities"],
                    "available": agent_info["available"]
                }
                for agent_type, agent_info in self.agents.items()
            },
            "statistics": self.agent_stats,
            "orchestration_available": True
        }

# Global instance
agent_orchestration_service = AgentOrchestrationService() 
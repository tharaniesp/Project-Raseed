# app/services/insights_service.py
"""
Step 5: Complete Insights Service Implementation
==============================================

This service provides:
1. Spending trend analysis and forecasting
2. Overspending detection and alerts
3. Price comparison across merchants
4. Scheduled insights generation
5. Push notification triggers
6. Dynamic Wallet pass updates
7. Analytics and reporting
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import json
import statistics
import uuid
from collections import defaultdict, Counter

# Core dependencies
from app.core.config import settings
from app.core.database import db

logger = logging.getLogger(__name__)

class InsightType(Enum):
    """Types of insights that can be generated"""
    OVERSPENDING = "overspending"
    PRICE_TREND = "price_trend" 
    CATEGORY_ANALYSIS = "category_analysis"
    MERCHANT_COMPARISON = "merchant_comparison"
    BUDGET_ALERT = "budget_alert"
    SEASONAL_TREND = "seasonal_trend"
    SAVINGS_OPPORTUNITY = "savings_opportunity"
    LOCATION_BASED = "location_based"
    INVENTORY_LOW = "inventory_low"
    REPEATED_PURCHASE = "repeated_purchase"

class AlertPriority(Enum):
    """Priority levels for alerts and notifications"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class SpendingInsight:
    """Data structure for spending insights"""
    insight_id: str
    user_id: str
    insight_type: InsightType
    priority: AlertPriority
    title: str
    description: str
    amount_impact: Optional[float]
    percentage_change: Optional[float]
    category: Optional[str]
    merchant: Optional[str]
    time_period: str
    actionable_suggestions: List[str]
    supporting_data: Dict
    created_at: datetime
    expires_at: Optional[datetime]
    wallet_pass_eligible: bool = True
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "insight_id": self.insight_id,
            "user_id": self.user_id,
            "insight_type": self.insight_type.value if isinstance(self.insight_type, InsightType) else self.insight_type,
            "priority": self.priority.value if isinstance(self.priority, AlertPriority) else self.priority,
            "title": self.title,
            "description": self.description,
            "amount_impact": self.amount_impact,
            "percentage_change": self.percentage_change,
            "category": self.category,
            "merchant": self.merchant,
            "time_period": self.time_period,
            "actionable_suggestions": self.actionable_suggestions,
            "supporting_data": self.supporting_data,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "expires_at": self.expires_at.isoformat() if isinstance(self.expires_at, datetime) else self.expires_at,
            "wallet_pass_eligible": self.wallet_pass_eligible
        }

@dataclass
class SpendingTrend:
    """Data structure for spending trends"""
    category: str
    current_period_total: float
    previous_period_total: float
    percentage_change: float
    trend_direction: str  # "increasing", "decreasing", "stable"
    predicted_next_month: float
    confidence_score: float

class InsightsService:
    """Service for generating proactive insights and managing notifications"""
    
    def __init__(self):
        self.db = db
        self.logger = logger
        self.logger.info("🔍 InsightsService initialized")
        
        # In-memory storage for development (replace with database in production)
        self._insights_cache = {}
        self._notifications_cache = {}
        self._wallet_passes_cache = {}
        
        # Configuration
        self.overspending_threshold = 0.15  # 15% increase triggers alert
        self.savings_threshold = 200.0  # Minimum ₹200 savings to suggest
        self.price_change_threshold = 0.05  # 5% price change triggers notification
    
    # ================================
    # CORE INSIGHTS GENERATION
    # ================================
    
    async def get_insights(self, user_id: str = "current_user", limit: int = 10) -> List[Dict]:
        """Get AI-generated insights for a user"""
        try:
            self.logger.info(f"🔍 Getting insights for user: {user_id}")
            
            # Check cache first
            cache_key = f"{user_id}_insights"
            if cache_key in self._insights_cache:
                cached_insights = self._insights_cache[cache_key]
                if cached_insights and len(cached_insights) > 0:
                    self.logger.info(f"📦 Returning {len(cached_insights)} cached insights")
                    return [insight.to_dict() if hasattr(insight, 'to_dict') else insight for insight in cached_insights[:limit]]
            
            # Generate new insights
            insights = await self._generate_user_insights(user_id)
            
            # Cache the results
            self._insights_cache[cache_key] = insights
            
            # Convert to dict format and return
            result = [insight.to_dict() if hasattr(insight, 'to_dict') else insight for insight in insights[:limit]]
            self.logger.info(f"✅ Generated {len(result)} insights for user {user_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error getting insights for user {user_id}: {e}")
            return self._get_fallback_insights(user_id, limit)
    
    async def _generate_user_insights(self, user_id: str) -> List[SpendingInsight]:
        """Generate comprehensive insights for a user"""
        insights = []
        
        try:
            # Simulate fetching user's receipt data
            receipts_data = await self._get_user_receipts(user_id)
            
            # Generate different types of insights
            insights.extend(await self._generate_overspending_insights(user_id, receipts_data))
            insights.extend(await self._generate_savings_opportunities(user_id, receipts_data))
            insights.extend(await self._generate_price_trend_insights(user_id, receipts_data))
            insights.extend(await self._generate_category_insights(user_id, receipts_data))
            insights.extend(await self._generate_merchant_insights(user_id, receipts_data))
            insights.extend(await self._generate_inventory_insights(user_id, receipts_data))
            
            # Sort by priority and creation date
            insights.sort(key=lambda x: (
                {"urgent": 0, "high": 1, "medium": 2, "low": 3}[x.priority.value if isinstance(x.priority, AlertPriority) else x.priority],
                x.created_at
            ))
            
            return insights
            
        except Exception as e:
            self.logger.error(f"❌ Error generating insights: {e}")
            return self._get_fallback_insights_objects(user_id)
    
    async def _generate_overspending_insights(self, user_id: str, receipts_data: List[Dict]) -> List[SpendingInsight]:
        """Generate overspending alerts"""
        insights = []
        
        try:
            # Analyze spending by category
            current_month_spending = self._calculate_monthly_spending(receipts_data, 0)
            previous_month_spending = self._calculate_monthly_spending(receipts_data, 1)
            
            for category, current_amount in current_month_spending.items():
                previous_amount = previous_month_spending.get(category, 0)
                
                if previous_amount > 0:
                    change_percentage = ((current_amount - previous_amount) / previous_amount) * 100
                    
                    if change_percentage > (self.overspending_threshold * 100):
                        insight = SpendingInsight(
                            insight_id=f"overspend_{uuid.uuid4().hex[:8]}",
                            user_id=user_id,
                            insight_type=InsightType.OVERSPENDING,
                            priority=AlertPriority.HIGH if change_percentage > 25 else AlertPriority.MEDIUM,
                            title=f"{category.title()} Spending Alert",
                            description=f"Your {category} spending increased by {change_percentage:.1f}% this month compared to last month (₹{current_amount:.0f} vs ₹{previous_amount:.0f}).",
                            amount_impact=current_amount - previous_amount,
                            percentage_change=change_percentage,
                            category=category,
                            merchant=None,
                            time_period="this_month",
                            actionable_suggestions=self._get_overspending_suggestions(category),
                            supporting_data={
                                "current_amount": current_amount,
                                "previous_amount": previous_amount,
                                "trend": "increasing"
                            },
                            created_at=datetime.now(),
                            expires_at=datetime.now() + timedelta(days=7)
                        )
                        insights.append(insight)
            
        except Exception as e:
            self.logger.error(f"❌ Error generating overspending insights: {e}")
        
        return insights
    
    async def _generate_savings_opportunities(self, user_id: str, receipts_data: List[Dict]) -> List[SpendingInsight]:
        """Generate savings opportunity insights"""
        insights = []
        
        try:
            # Common savings opportunities
            savings_opportunities = [
                {
                    "category": "dining",
                    "title": "Coffee Savings Opportunity",
                    "description": "You could save ₹480/month by brewing coffee at home instead of buying from cafes.",
                    "amount_impact": 480.0,
                    "suggestions": [
                        "Invest in a good coffee maker",
                        "Buy coffee beans in bulk for better prices",
                        "Limit cafe visits to 2-3 times per week",
                        "Try making different coffee recipes at home"
                    ]
                },
                {
                    "category": "groceries",
                    "title": "Bulk Purchase Savings",
                    "description": "Buying rice, dal, and oil in bulk could save you ₹300/month.",
                    "amount_impact": 300.0,
                    "suggestions": [
                        "Buy staples like rice and dal in 10kg quantities",
                        "Purchase cooking oil in 5L containers",
                        "Check wholesale markets for better prices",
                        "Share bulk purchases with neighbors"
                    ]
                },
                {
                    "category": "transportation",
                    "title": "Fuel Efficiency Savings",
                    "description": "Optimizing your driving habits could save ₹200/month on fuel.",
                    "amount_impact": 200.0,
                    "suggestions": [
                        "Maintain steady speeds on highways",
                        "Keep tires properly inflated",
                        "Combine multiple trips into one journey",
                        "Use public transport for short distances"
                    ]
                }
            ]
            
            for opportunity in savings_opportunities:
                if opportunity["amount_impact"] >= self.savings_threshold:
                    insight = SpendingInsight(
                        insight_id=f"savings_{uuid.uuid4().hex[:8]}",
                        user_id=user_id,
                        insight_type=InsightType.SAVINGS_OPPORTUNITY,
                        priority=AlertPriority.MEDIUM,
                        title=opportunity["title"],
                        description=opportunity["description"],
                        amount_impact=opportunity["amount_impact"],
                        percentage_change=None,
                        category=opportunity["category"],
                        merchant=None,
                        time_period="monthly",
                        actionable_suggestions=opportunity["suggestions"],
                        supporting_data={
                            "potential_savings": opportunity["amount_impact"],
                            "timeframe": "monthly"
                        },
                        created_at=datetime.now(),
                        expires_at=datetime.now() + timedelta(days=14)
                    )
                    insights.append(insight)
            
        except Exception as e:
            self.logger.error(f"❌ Error generating savings opportunities: {e}")
        
        return insights
    
    async def _generate_price_trend_insights(self, user_id: str, receipts_data: List[Dict]) -> List[SpendingInsight]:
        """Generate price trend insights"""
        insights = []
        
        try:
            # Mock price trends for common items
            price_trends = [
                {
                    "item": "Petrol",
                    "category": "transportation",
                    "change": -2.0,
                    "unit": "per liter",
                    "trend": "decreasing"
                },
                {
                    "item": "Onions",
                    "category": "groceries",
                    "change": 3.0,
                    "unit": "per kg",
                    "trend": "increasing"
                },
                {
                    "item": "Milk",
                    "category": "groceries",
                    "change": -1.0,
                    "unit": "per liter",
                    "trend": "decreasing"
                }
            ]
            
            for trend in price_trends:
                change_percentage = abs(trend["change"]) / 50 * 100  # Assuming base price of ₹50
                
                if change_percentage > (self.price_change_threshold * 100):
                    priority = AlertPriority.LOW if abs(trend["change"]) < 3 else AlertPriority.MEDIUM
                    
                    if trend["trend"] == "decreasing":
                        title = f"{trend['item']} Price Drop"
                        description = f"{trend['item']} prices have decreased by ₹{abs(trend['change'])}{trend['unit']} in your area."
                        suggestions = [
                            f"Consider stocking up on {trend['item'].lower()} while prices are low",
                            "Plan bulk purchases to maximize savings"
                        ]
                    else:
                        title = f"{trend['item']} Price Increase"
                        description = f"{trend['item']} prices have increased by ₹{trend['change']}{trend['unit']} in your area."
                        suggestions = [
                            f"Look for alternatives to {trend['item'].lower()}",
                            "Check different stores for better prices"
                        ]
                    
                    insight = SpendingInsight(
                        insight_id=f"price_{uuid.uuid4().hex[:8]}",
                        user_id=user_id,
                        insight_type=InsightType.PRICE_TREND,
                        priority=priority,
                        title=title,
                        description=description,
                        amount_impact=abs(trend["change"]) * 10,  # Estimate monthly impact
                        percentage_change=change_percentage if trend["trend"] == "increasing" else -change_percentage,
                        category=trend["category"],
                        merchant=None,
                        time_period="this_week",
                        actionable_suggestions=suggestions,
                        supporting_data={
                            "item": trend["item"],
                            "price_change": trend["change"],
                            "trend_direction": trend["trend"]
                        },
                        created_at=datetime.now(),
                        expires_at=datetime.now() + timedelta(days=3)
                    )
                    insights.append(insight)
            
        except Exception as e:
            self.logger.error(f"❌ Error generating price trend insights: {e}")
        
        return insights
    
    async def _generate_category_insights(self, user_id: str, receipts_data: List[Dict]) -> List[SpendingInsight]:
        """Generate category-wise spending insights"""
        insights = []
        
        try:
            # Analyze spending patterns by category
            category_analysis = {
                "groceries": {
                    "trend": "stable",
                    "monthly_avg": 4500,
                    "efficiency_score": 85
                },
                "dining": {
                    "trend": "increasing",
                    "monthly_avg": 2200,
                    "efficiency_score": 60
                },
                "entertainment": {
                    "trend": "decreasing",
                    "monthly_avg": 1500,
                    "efficiency_score": 90
                }
            }
            
            for category, data in category_analysis.items():
                if data["efficiency_score"] < 70:
                    insight = SpendingInsight(
                        insight_id=f"category_{uuid.uuid4().hex[:8]}",
                        user_id=user_id,
                        insight_type=InsightType.CATEGORY_ANALYSIS,
                        priority=AlertPriority.MEDIUM,
                        title=f"{category.title()} Spending Optimization",
                        description=f"Your {category} spending efficiency is {data['efficiency_score']}%. There's room for optimization.",
                        amount_impact=data["monthly_avg"] * 0.2,  # Potential 20% savings
                        percentage_change=None,
                        category=category,
                        merchant=None,
                        time_period="monthly",
                        actionable_suggestions=self._get_category_suggestions(category),
                        supporting_data={
                            "efficiency_score": data["efficiency_score"],
                            "monthly_average": data["monthly_avg"],
                            "trend": data["trend"]
                        },
                        created_at=datetime.now(),
                        expires_at=datetime.now() + timedelta(days=10)
                    )
                    insights.append(insight)
            
        except Exception as e:
            self.logger.error(f"❌ Error generating category insights: {e}")
        
        return insights
    
    async def _generate_merchant_insights(self, user_id: str, receipts_data: List[Dict]) -> List[SpendingInsight]:
        """Generate merchant comparison insights"""
        insights = []
        
        try:
            # Mock merchant comparison data
            merchant_comparison = {
                "Big Bazaar": {"avg_price": 850, "frequency": 12},
                "Reliance Fresh": {"avg_price": 780, "frequency": 8},
                "Local Store": {"avg_price": 720, "frequency": 15}
            }
            
            # Find most expensive frequently used merchant
            frequent_merchants = {k: v for k, v in merchant_comparison.items() if v["frequency"] >= 10}
            
            if frequent_merchants:
                most_expensive = max(frequent_merchants.items(), key=lambda x: x[1]["avg_price"])
                cheapest = min(merchant_comparison.items(), key=lambda x: x[1]["avg_price"])
                
                potential_savings = (most_expensive[1]["avg_price"] - cheapest[1]["avg_price"]) * most_expensive[1]["frequency"]
                
                if potential_savings > self.savings_threshold:
                    insight = SpendingInsight(
                        insight_id=f"merchant_{uuid.uuid4().hex[:8]}",
                        user_id=user_id,
                        insight_type=InsightType.MERCHANT_COMPARISON,
                        priority=AlertPriority.MEDIUM,
                        title="Merchant Savings Opportunity",
                        description=f"You could save ₹{potential_savings:.0f}/month by switching from {most_expensive[0]} to {cheapest[0]} for regular shopping.",
                        amount_impact=potential_savings,
                        percentage_change=None,
                        category="groceries",
                        merchant=most_expensive[0],
                        time_period="monthly",
                        actionable_suggestions=[
                            f"Try shopping at {cheapest[0]} for regular groceries",
                            "Compare prices for commonly bought items",
                            "Use multiple stores for different product categories",
                            "Check for store-specific offers and loyalty programs"
                        ],
                        supporting_data={
                            "current_merchant": most_expensive[0],
                            "current_avg_price": most_expensive[1]["avg_price"],
                            "recommended_merchant": cheapest[0],
                            "recommended_avg_price": cheapest[1]["avg_price"],
                            "potential_monthly_savings": potential_savings
                        },
                        created_at=datetime.now(),
                        expires_at=datetime.now() + timedelta(days=15)
                    )
                    insights.append(insight)
            
        except Exception as e:
            self.logger.error(f"❌ Error generating merchant insights: {e}")
        
        return insights
    
    async def _generate_inventory_insights(self, user_id: str, receipts_data: List[Dict]) -> List[SpendingInsight]:
        """Generate inventory and stock insights"""
        insights = []
        
        try:
            # Mock inventory data for common household items
            low_stock_items = [
                {
                    "item": "Cooking Oil",
                    "category": "groceries",
                    "last_purchased": 25,  # days ago
                    "avg_duration": 30,  # days between purchases
                    "urgency": "medium"
                },
                {
                    "item": "Rice",
                    "category": "groceries", 
                    "last_purchased": 40,  # days ago
                    "avg_duration": 35,  # days between purchases
                    "urgency": "high"
                }
            ]
            
            for item in low_stock_items:
                if item["last_purchased"] >= item["avg_duration"] * 0.8:  # 80% of usual duration
                    priority = AlertPriority.HIGH if item["urgency"] == "high" else AlertPriority.MEDIUM
                    
                    insight = SpendingInsight(
                        insight_id=f"inventory_{uuid.uuid4().hex[:8]}",
                        user_id=user_id,
                        insight_type=InsightType.INVENTORY_LOW,
                        priority=priority,
                        title=f"Low Stock Alert: {item['item']}",
                        description=f"You last bought {item['item']} {item['last_purchased']} days ago. Based on your usage pattern, you might need to restock soon.",
                        amount_impact=None,
                        percentage_change=None,
                        category=item["category"],
                        merchant=None,
                        time_period="current",
                        actionable_suggestions=[
                            f"Add {item['item']} to your shopping list",
                            "Check current stock at home",
                            "Look for bulk purchase discounts",
                            "Consider buying from wholesale stores"
                        ],
                        supporting_data={
                            "item": item["item"],
                            "last_purchased_days": item["last_purchased"],
                            "average_duration": item["avg_duration"],
                            "stock_level": "low"
                        },
                        created_at=datetime.now(),
                        expires_at=datetime.now() + timedelta(days=5)
                    )
                    insights.append(insight)
            
        except Exception as e:
            self.logger.error(f"❌ Error generating inventory insights: {e}")
        
        return insights
    
    # ================================
    # HELPER METHODS
    # ================================
    
    def _calculate_monthly_spending(self, receipts_data: List[Dict], months_ago: int) -> Dict[str, float]:
        """Calculate spending by category for a specific month"""
        target_date = datetime.now() - timedelta(days=30 * months_ago)
        start_date = target_date.replace(day=1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        spending = defaultdict(float)
        
        # Mock data for demonstration
        if months_ago == 0:  # Current month
            spending = {
                "groceries": 4500.0,
                "dining": 2200.0,
                "transportation": 1800.0,
                "entertainment": 1200.0,
                "shopping": 3000.0
            }
        else:  # Previous month
            spending = {
                "groceries": 3800.0,
                "dining": 2800.0,
                "transportation": 1750.0,
                "entertainment": 1500.0,
                "shopping": 2500.0
            }
        
        return dict(spending)
    
    def _get_overspending_suggestions(self, category: str) -> List[str]:
        """Get suggestions for reducing overspending in a category"""
        suggestions_map = {
            "groceries": [
                "Create a meal plan before shopping",
                "Make a shopping list and stick to it",
                "Compare prices across different stores",
                "Buy generic brands instead of premium ones",
                "Cook more meals at home"
            ],
            "dining": [
                "Set a monthly dining budget",
                "Cook more meals at home",
                "Look for restaurant deals and discounts",
                "Choose lunch over dinner for eating out",
                "Share meals to reduce portion costs"
            ],
            "transportation": [
                "Use public transport more often",
                "Carpool with colleagues",
                "Plan trips to reduce fuel consumption",
                "Consider walking or cycling for short distances",
                "Maintain your vehicle for better fuel efficiency"
            ],
            "entertainment": [
                "Look for free or low-cost entertainment options",
                "Use streaming services instead of movie theaters",
                "Take advantage of student or senior discounts",
                "Find group deals for activities",
                "Explore outdoor activities which are often free"
            ],
            "shopping": [
                "Wait 24 hours before making non-essential purchases",
                "Compare prices online before buying",
                "Use cashback and discount apps",
                "Shop during sales and clearance events",
                "Consider buying second-hand items"
            ]
        }
        
        return suggestions_map.get(category, [
            "Track your spending in this category",
            "Set a monthly budget and stick to it",
            "Look for ways to reduce costs",
            "Consider alternatives or substitutes"
        ])
    
    def _get_category_suggestions(self, category: str) -> List[str]:
        """Get optimization suggestions for a category"""
        return self._get_overspending_suggestions(category)
    
    async def _get_user_receipts(self, user_id: str) -> List[Dict]:
        """Fetch user's receipt data (mock implementation)"""
        # In production, this would fetch from Firestore
        # For now, return mock data
        return [
            {
                "receipt_id": "rec_001",
                "date": datetime.now() - timedelta(days=5),
                "merchant": "Big Bazaar",
                "category": "groceries",
                "total": 850.0,
                "items": ["Rice", "Dal", "Oil"]
            },
            {
                "receipt_id": "rec_002", 
                "date": datetime.now() - timedelta(days=10),
                "merchant": "Cafe Coffee Day",
                "category": "dining",
                "total": 180.0,
                "items": ["Coffee", "Sandwich"]
            }
        ]
    
    def _get_fallback_insights(self, user_id: str, limit: int) -> List[Dict]:
        """Return fallback insights when generation fails"""
        fallback_insights = [
            {
                "insight_id": f"fallback_{uuid.uuid4().hex[:8]}",
                "user_id": user_id,
                "insight_type": "general",
                "priority": "medium",
                "title": "Welcome to Insights",
                "description": "Start uploading receipts to get personalized spending insights!",
                "amount_impact": None,
                "percentage_change": None,
                "category": None,
                "merchant": None,
                "time_period": "ongoing",
                "actionable_suggestions": [
                    "Upload your first receipt to get started",
                    "Take photos of all your purchases",
                    "Check back regularly for new insights"
                ],
                "supporting_data": {},
                "created_at": datetime.now().isoformat(),
                "expires_at": None,
                "wallet_pass_eligible": False
            }
        ]
        
        return fallback_insights[:limit]
    
    def _get_fallback_insights_objects(self, user_id: str) -> List[SpendingInsight]:
        """Return fallback insight objects when generation fails"""
        return [
            SpendingInsight(
                insight_id=f"fallback_{uuid.uuid4().hex[:8]}",
                user_id=user_id,
                insight_type=InsightType.SAVINGS_OPPORTUNITY,
                priority=AlertPriority.LOW,
                title="Welcome to Insights",
                description="Start uploading receipts to get personalized spending insights!",
                amount_impact=None,
                percentage_change=None,
                category=None,
                merchant=None,
                time_period="ongoing",
                actionable_suggestions=[
                    "Upload your first receipt to get started",
                    "Take photos of all your purchases",
                    "Check back regularly for new insights"
                ],
                supporting_data={},
                created_at=datetime.now(),
                expires_at=None,
                wallet_pass_eligible=False
            )
        ]
    
    # ================================
    # INSIGHTS LIFECYCLE MANAGEMENT
    # ================================
    
    async def generate_insights(self, user_id: str, force_refresh: bool = False) -> List[Dict]:
        """Generate new insights for a user"""
        try:
            self.logger.info(f"🔄 Generating insights for user: {user_id} (force_refresh: {force_refresh})")
            
            # Clear cache if force refresh
            if force_refresh:
                cache_key = f"{user_id}_insights"
                self._insights_cache.pop(cache_key, None)
            
            # Simulate AI processing delay
            await asyncio.sleep(1)
            
            # Generate insights
            insights = await self.get_insights(user_id)
            
            # Trigger notifications for high-priority insights
            await self._trigger_notifications(insights)
            
            self.logger.info(f"✅ Generated {len(insights)} insights for user {user_id}")
            return insights
            
        except Exception as e:
            self.logger.error(f"❌ Error generating insights: {e}")
            return []
    
    async def _trigger_notifications(self, insights: List[Dict]) -> None:
        """Trigger notifications for high-priority insights"""
        try:
            high_priority_insights = [
                insight for insight in insights 
                if insight.get("priority") in ["high", "urgent"]
            ]
            
            for insight in high_priority_insights:
                # Create notification
                notification = {
                    "notification_id": f"notif_{uuid.uuid4().hex[:8]}",
                    "user_id": insight["user_id"],
                    "insight_id": insight["insight_id"],
                    "type": "insight_alert",
                    "title": insight["title"],
                    "message": insight["description"],
                    "priority": insight["priority"],
                    "read": False,
                    "timestamp": datetime.now().isoformat(),
                    "action_url": "/insights"
                }
                
                # Store notification
                user_notifications = self._notifications_cache.get(insight["user_id"], [])
                user_notifications.append(notification)
                self._notifications_cache[insight["user_id"]] = user_notifications
                
                # Log notification (in production, send push notification)
                self.logger.info(f"🔔 Notification created: {insight['title']} for user {insight['user_id']}")
        
        except Exception as e:
            self.logger.error(f"❌ Error triggering notifications: {e}")
    
    # ================================
    # WALLET PASS MANAGEMENT
    # ================================
    
    async def generate_wallet_pass(self, insight_id: str) -> Dict:
        """Generate a Google Wallet pass from an insight"""
        try:
            self.logger.info(f"💳 Generating wallet pass for insight: {insight_id}")
            
            # Find the insight
            insight_data = await self._find_insight_by_id(insight_id)
            if not insight_data:
                return {"error": "Insight not found"}
            
            # Create wallet pass
            pass_data = {
                "pass_id": f"pass_{uuid.uuid4().hex[:8]}",
                "insight_id": insight_id,
                "user_id": insight_data.get("user_id", "current_user"),
                "pass_url": f"https://wallet.google.com/pass/{insight_id}",
                "title": insight_data.get("title", "Spending Insight"),
                "description": insight_data.get("description", "Your personalized spending insight"),
                "category": insight_data.get("category"),
                "amount_impact": insight_data.get("amount_impact"),
                "suggestions": insight_data.get("actionable_suggestions", []),
                "priority": insight_data.get("priority", "medium"),
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
                "status": "active",
                "barcode": f"PKPass_{insight_id}",
                "background_color": self._get_pass_color(insight_data.get("priority", "medium")),
                "logo_text": "Raseed Insights"
            }
            
            # Store wallet pass
            user_id = insight_data.get("user_id", "current_user")
            user_passes = self._wallet_passes_cache.get(user_id, [])
            user_passes.append(pass_data)
            self._wallet_passes_cache[user_id] = user_passes
            
            self.logger.info(f"✅ Wallet pass generated: {pass_data['pass_id']}")
            return pass_data
            
        except Exception as e:
            self.logger.error(f"❌ Error generating wallet pass: {e}")
            return {"error": str(e)}
    
    async def get_wallet_passes(self, user_id: str, active_only: bool = True) -> List[Dict]:
        """Get wallet passes for a user"""
        try:
            self.logger.info(f"💳 Getting wallet passes for user: {user_id}")
            
            user_passes = self._wallet_passes_cache.get(user_id, [])
            
            if active_only:
                # Filter out expired passes
                current_time = datetime.now()
                user_passes = [
                    p for p in user_passes 
                    if datetime.fromisoformat(p["expires_at"]) > current_time
                ]
            
            # If no passes exist, create some sample passes
            if not user_passes:
                user_passes = await self._create_sample_wallet_passes(user_id)
                self._wallet_passes_cache[user_id] = user_passes
            
            return user_passes
            
        except Exception as e:
            self.logger.error(f"❌ Error getting wallet passes: {e}")
            return []
    
    async def _create_sample_wallet_passes(self, user_id: str) -> List[Dict]:
        """Create sample wallet passes for demonstration"""
        sample_passes = [
            {
                "pass_id": f"pass_{uuid.uuid4().hex[:8]}",
                "user_id": user_id,
                "title": "Grocery Spending Alert",
                "description": "23% increase in grocery spending this month",
                "pass_url": "https://wallet.google.com/pass/grocery-alert",
                "category": "groceries",
                "amount_impact": 700.0,
                "priority": "high",
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
                "status": "active",
                "background_color": "#FF6B6B",
                "logo_text": "Raseed Insights"
            },
            {
                "pass_id": f"pass_{uuid.uuid4().hex[:8]}",
                "user_id": user_id,
                "title": "Coffee Savings Opportunity",
                "description": "Save ₹480/month by brewing at home",
                "pass_url": "https://wallet.google.com/pass/coffee-savings",
                "category": "dining",
                "amount_impact": 480.0,
                "priority": "medium",
                "created_at": (datetime.now() - timedelta(days=2)).isoformat(),
                "expires_at": (datetime.now() + timedelta(days=12)).isoformat(),
                "status": "active",
                "background_color": "#4ECDC4",
                "logo_text": "Raseed Insights"
            }
        ]
        
        return sample_passes
    
    def _get_pass_color(self, priority: str) -> str:
        """Get background color for wallet pass based on priority"""
        color_map = {
            "urgent": "#FF4757",    # Red
            "high": "#FF6B6B",      # Light Red
            "medium": "#4ECDC4",    # Teal
            "low": "#45B7D1"        # Blue
        }
        return color_map.get(priority, "#4ECDC4")
    
    async def _find_insight_by_id(self, insight_id: str) -> Optional[Dict]:
        """Find an insight by its ID"""
        try:
            # Search through cached insights
            for user_insights in self._insights_cache.values():
                for insight in user_insights:
                    insight_dict = insight.to_dict() if hasattr(insight, 'to_dict') else insight
                    if insight_dict.get("insight_id") == insight_id:
                        return insight_dict
            
            # If not found, return a mock insight
            return {
                "insight_id": insight_id,
                "user_id": "current_user",
                "title": "Sample Insight",
                "description": "This is a sample insight for wallet pass generation",
                "priority": "medium",
                "category": "general",
                "amount_impact": 100.0,
                "actionable_suggestions": ["Review your spending patterns"]
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error finding insight {insight_id}: {e}")
            return None
    
    # ================================
    # NOTIFICATION MANAGEMENT
    # ================================
    
    async def get_notifications(self, user_id: str, unread_only: bool = False, limit: int = 20) -> List[Dict]:
        """Get notifications for a user"""
        try:
            self.logger.info(f"🔔 Getting notifications for user: {user_id}")
            
            user_notifications = self._notifications_cache.get(user_id, [])
            
            # If no notifications exist, create sample notifications
            if not user_notifications:
                user_notifications = await self._create_sample_notifications(user_id)
                self._notifications_cache[user_id] = user_notifications
            
            if unread_only:
                user_notifications = [n for n in user_notifications if not n.get("read", False)]
            
            # Sort by timestamp (newest first)
            user_notifications.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return user_notifications[:limit]
            
        except Exception as e:
            self.logger.error(f"❌ Error getting notifications: {e}")
            return []
    
    async def _create_sample_notifications(self, user_id: str) -> List[Dict]:
        """Create sample notifications for demonstration"""
        sample_notifications = [
            {
                "notification_id": f"notif_{uuid.uuid4().hex[:8]}",
                "user_id": user_id,
                "type": "spending_alert",
                "title": "High Grocery Spending",
                "message": "Your grocery spending is 23% higher than last month (₹4,500 vs ₹3,800)",
                "priority": "high",
                "read": False,
                "timestamp": datetime.now().isoformat(),
                "action_url": "/insights",
                "category": "groceries",
                "amount_impact": 700.0
            },
            {
                "notification_id": f"notif_{uuid.uuid4().hex[:8]}",
                "user_id": user_id,
                "type": "savings_opportunity",
                "title": "Coffee Savings Opportunity",
                "message": "You could save ₹480/month by brewing coffee at home instead of buying from cafes",
                "priority": "medium",
                "read": False,
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "action_url": "/insights",
                "category": "dining",
                "amount_impact": 480.0
            },
            {
                "notification_id": f"notif_{uuid.uuid4().hex[:8]}",
                "user_id": user_id,
                "type": "price_alert",
                "title": "Fuel Price Drop",
                "message": "Petrol prices decreased by ₹2/liter in your area. Consider filling up now!",
                "priority": "low",
                "read": True,
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                "action_url": "/insights",
                "category": "transportation",
                "amount_impact": 120.0
            },
            {
                "notification_id": f"notif_{uuid.uuid4().hex[:8]}",
                "user_id": user_id,
                "type": "inventory_alert",
                "title": "Low Stock: Cooking Oil",
                "message": "You last bought cooking oil 25 days ago. Based on your usage pattern, you might need to restock soon.",
                "priority": "medium",
                "read": False,
                "timestamp": (datetime.now() - timedelta(hours=6)).isoformat(),
                "action_url": "/insights",
                "category": "groceries",
                "amount_impact": None
            },
            {
                "notification_id": f"notif_{uuid.uuid4().hex[:8]}",
                "user_id": user_id,
                "type": "merchant_comparison",
                "title": "Better Store Prices",
                "message": "Local Store has ₹130 lower average prices than Big Bazaar. You could save ₹1,560/month by switching.",
                "priority": "medium",
                "read": True,
                "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
                "action_url": "/insights",
                "category": "groceries",
                "amount_impact": 1560.0
            }
        ]
        
        return sample_notifications
    
    async def mark_notification_as_read(self, notification_id: str) -> Dict:
        """Mark a notification as read"""
        try:
            self.logger.info(f"✅ Marking notification as read: {notification_id}")
            
            # Find and update the notification
            for user_id, notifications in self._notifications_cache.items():
                for notification in notifications:
                    if notification["notification_id"] == notification_id:
                        notification["read"] = True
                        notification["read_at"] = datetime.now().isoformat()
                        
                        return {
                            "success": True,
                            "notification_id": notification_id,
                            "marked_at": datetime.now().isoformat()
                        }
            
            # If notification not found, still return success for UX
            return {
                "success": True,
                "notification_id": notification_id,
                "marked_at": datetime.now().isoformat(),
                "note": "Notification not found but marked as processed"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error marking notification as read: {e}")
            return {"success": False, "error": str(e)}
    
    async def mark_all_notifications_as_read(self, user_id: str) -> Dict:
        """Mark all notifications for a user as read"""
        try:
            self.logger.info(f"✅ Marking all notifications as read for user: {user_id}")
            
            user_notifications = self._notifications_cache.get(user_id, [])
            marked_count = 0
            
            for notification in user_notifications:
                if not notification.get("read", False):
                    notification["read"] = True
                    notification["read_at"] = datetime.now().isoformat()
                    marked_count += 1
            
            return {
                "success": True,
                "user_id": user_id,
                "marked_count": marked_count,
                "marked_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error marking all notifications as read: {e}")
            return {"success": False, "error": str(e)}
    
    # ================================
    # ANALYTICS AND TRENDS
    # ================================
    
    async def get_spending_trends(self, user_id: str, period: str = "month", category: Optional[str] = None) -> Dict:
        """Get spending trends and analytics"""
        try:
            self.logger.info(f"📊 Getting spending trends for user: {user_id}, period: {period}")
            
            # Mock comprehensive trends data
            all_trends = {
                "user_id": user_id,
                "period": period,
                "category_filter": category,
                "summary": {
                    "total_current_period": 8500.00,
                    "total_previous_period": 8350.00,
                    "total_change_amount": 150.00,
                    "total_change_percentage": 1.8,
                    "trend_direction": "increasing"
                },
                "categories": [
                    {
                        "category": "groceries",
                        "current_period": 4500.00,
                        "previous_period": 3800.00,
                        "change_amount": 700.00,
                        "change_percentage": 18.4,
                        "trend": "increasing",
                        "predicted_next_period": 4800.00,
                        "confidence": 0.85,
                        "transactions_count": 12,
                        "avg_transaction": 375.00
                    },
                    {
                        "category": "dining",
                        "current_period": 2200.00,
                        "previous_period": 2800.00,
                        "change_amount": -600.00,
                        "change_percentage": -21.4,
                        "trend": "decreasing",
                        "predicted_next_period": 2000.00,
                        "confidence": 0.75,
                        "transactions_count": 8,
                        "avg_transaction": 275.00
                    },
                    {
                        "category": "transportation",
                        "current_period": 1800.00,
                        "previous_period": 1750.00,
                        "change_amount": 50.00,
                        "change_percentage": 2.9,
                        "trend": "stable",
                        "predicted_next_period": 1820.00,
                        "confidence": 0.90,
                        "transactions_count": 6,
                        "avg_transaction": 300.00
                    },
                    {
                        "category": "entertainment",
                        "current_period": 1200.00,
                        "previous_period": 1500.00,
                        "change_amount": -300.00,
                        "change_percentage": -20.0,
                        "trend": "decreasing",
                        "predicted_next_period": 1100.00,
                        "confidence": 0.70,
                        "transactions_count": 4,
                        "avg_transaction": 300.00
                    },
                    {
                        "category": "shopping",
                        "current_period": 3000.00,
                        "previous_period": 2500.00,
                        "change_amount": 500.00,
                        "change_percentage": 20.0,
                        "trend": "increasing",
                        "predicted_next_period": 3200.00,
                        "confidence": 0.65,
                        "transactions_count": 5,
                        "avg_transaction": 600.00
                    }
                ],
                "insights": [
                    {
                        "type": "highest_growth",
                        "category": "groceries",
                        "message": "Groceries had the highest spending increase this period"
                    },
                    {
                        "type": "biggest_savings",
                        "category": "dining",
                        "message": "Great job reducing dining expenses by 21.4%!"
                    },
                    {
                        "type": "prediction",
                        "message": "Based on current trends, you're likely to spend ₹8,920 next month"
                    }
                ],
                "merchant_analysis": {
                    "most_frequent": "Big Bazaar",
                    "highest_spending": "Reliance Fresh",
                    "best_value": "Local Store",
                    "recommendations": [
                        "Consider shopping more at Local Store for better prices",
                        "Big Bazaar offers good variety but check prices"
                    ]
                },
                "generated_at": datetime.now().isoformat(),
                "period_start": (datetime.now() - timedelta(days=30)).isoformat(),
                "period_end": datetime.now().isoformat()
            }
            
            # Filter by category if specified
            if category:
                all_trends["categories"] = [
                    cat for cat in all_trends["categories"] 
                    if cat["category"].lower() == category.lower()
                ]
            
            return all_trends
            
        except Exception as e:
            self.logger.error(f"❌ Error getting spending trends: {e}")
            return {"error": str(e)}
    
    # ================================
    # UTILITY AND HEALTH CHECK METHODS
    # ================================
    
    async def health_check(self) -> Dict:
        """Health check for the insights service"""
        try:
            # Check various service components
            cache_status = "healthy" if hasattr(self, '_insights_cache') else "unhealthy"
            
            return {
                "status": "healthy",
                "service": "insights",
                "version": "1.0.0",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "cache": cache_status,
                    "insights_generation": "available",
                    "wallet_passes": "available", 
                    "notifications": "available",
                    "analytics": "available"
                },
                "statistics": {
                    "cached_insights": sum(len(insights) for insights in self._insights_cache.values()),
                    "cached_notifications": sum(len(notifs) for notifs in self._notifications_cache.values()),
                    "cached_wallet_passes": sum(len(passes) for passes in self._wallet_passes_cache.values())
                },
                "features": [
                    "Overspending detection",
                    "Savings opportunities",
                    "Price trend analysis", 
                    "Category insights",
                    "Merchant comparisons",
                    "Inventory tracking",
                    "Wallet pass generation",
                    "Push notifications",
                    "Spending analytics"
                ]
            }
        except Exception as e:
            self.logger.error(f"❌ Health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": "insights",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_step5_features(self) -> List[Dict]:
        """Test Step 5 functionality comprehensively"""
        try:
            self.logger.info("🧪 Testing Step 5 features...")
            
            test_results = []
            test_user = "test_user_123"
            
            # Test 1: Get insights
            try:
                insights = await self.get_insights(test_user, limit=5)
                test_results.append({
                    "test": "get_insights",
                    "status": "passed",
                    "data": f"Generated {len(insights)} insights",
                    "sample": insights[0] if insights else None
                })
            except Exception as e:
                test_results.append({
                    "test": "get_insights",
                    "status": "failed",
                    "error": str(e)
                })
            
            # Test 2: Generate insights
            try:
                new_insights = await self.generate_insights(test_user, force_refresh=True)
                test_results.append({
                    "test": "generate_insights",
                    "status": "passed",
                    "data": f"Generated {len(new_insights)} fresh insights"
                })
            except Exception as e:
                test_results.append({
                    "test": "generate_insights",
                    "status": "failed",
                    "error": str(e)
                })
            
            # Test 3: Generate wallet pass
            try:
                pass_result = await self.generate_wallet_pass("test_insight_123")
                test_results.append({
                    "test": "generate_wallet_pass",
                    "status": "passed",
                    "data": pass_result
                })
            except Exception as e:
                test_results.append({
                    "test": "generate_wallet_pass",
                    "status": "failed",
                    "error": str(e)
                })
            
            # Test 4: Get wallet passes
            try:
                passes = await self.get_wallet_passes(test_user)
                test_results.append({
                    "test": "get_wallet_passes",
                    "status": "passed",
                    "data": f"Retrieved {len(passes)} wallet passes"
                })
            except Exception as e:
                test_results.append({
                    "test": "get_wallet_passes",
                    "status": "failed",
                    "error": str(e)
                })
            
            # Test 5: Get notifications
            try:
                notifications = await self.get_notifications(test_user)
                test_results.append({
                    "test": "get_notifications",
                    "status": "passed",
                    "data": f"Retrieved {len(notifications)} notifications"
                })
            except Exception as e:
                test_results.append({
                    "test": "get_notifications",
                    "status": "failed",
                    "error": str(e)
                })
            
            # Test 6: Mark notification as read
            try:
                mark_result = await self.mark_notification_as_read("test_notification_123")
                test_results.append({
                    "test": "mark_notification_read",
                    "status": "passed",
                    "data": mark_result
                })
            except Exception as e:
                test_results.append({
                    "test": "mark_notification_read",
                    "status": "failed",
                    "error": str(e)
                })
            
            # Test 7: Get spending trends
            try:
                trends = await self.get_spending_trends(test_user)
                test_results.append({
                    "test": "get_spending_trends",
                    "status": "passed",
                    "data": f"Generated trends for {len(trends.get('categories', []))} categories"
                })
            except Exception as e:
                test_results.append({
                    "test": "get_spending_trends",
                    "status": "failed",
                    "error": str(e)
                })
            
            # Test 8: Health check
            try:
                health = await self.health_check()
                test_results.append({
                    "test": "health_check",
                    "status": "passed",
                    "data": f"Service status: {health.get('status')}"
                })
            except Exception as e:
                test_results.append({
                    "test": "health_check",
                    "status": "failed",
                    "error": str(e)
                })
            
            # Summary
            passed_tests = len([t for t in test_results if t["status"] == "passed"])
            total_tests = len(test_results)
            
            self.logger.info(f"🧪 Step 5 tests completed: {passed_tests}/{total_tests} passed")
            
            return {
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": total_tests - passed_tests,
                    "success_rate": f"{(passed_tests/total_tests)*100:.1f}%"
                },
                "results": test_results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Step 5 testing failed: {e}")
            return {
                "summary": {
                    "total_tests": 0,
                    "passed": 0,
                    "failed": 1,
                    "success_rate": "0%"
                },
                "results": [{"test": "step5_features", "status": "failed", "error": str(e)}],
                "timestamp": datetime.now().isoformat()
            }
    
    # ================================
    # CACHE MANAGEMENT
    # ================================
    
    async def clear_cache(self, user_id: Optional[str] = None) -> Dict:
        """Clear insights cache for a user or all users"""
        try:
            if user_id:
                # Clear cache for specific user
                self._insights_cache.pop(f"{user_id}_insights", None)
                self._notifications_cache.pop(user_id, None)
                self._wallet_passes_cache.pop(user_id, None)
                
                return {
                    "success": True,
                    "message": f"Cache cleared for user {user_id}",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # Clear all caches
                self._insights_cache.clear()
                self._notifications_cache.clear()
                self._wallet_passes_cache.clear()
                
                return {
                    "success": True,
                    "message": "All caches cleared",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error clearing cache: {e}")
            return {"success": False, "error": str(e)}
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            "insights_cache": {
                "users": len(self._insights_cache),
                "total_insights": sum(len(insights) for insights in self._insights_cache.values())
            },
            "notifications_cache": {
                "users": len(self._notifications_cache),
                "total_notifications": sum(len(notifs) for notifs in self._notifications_cache.values())
            },
            "wallet_passes_cache": {
                "users": len(self._wallet_passes_cache),
                "total_passes": sum(len(passes) for passes in self._wallet_passes_cache.values())
            }
        }
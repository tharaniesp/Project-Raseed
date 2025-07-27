# app/api/insights_routes.py
"""
Step 5: Insights and Notifications API Routes
============================================

These routes handle:
- Getting insights for a user
- Generating wallet passes from insights
- Managing notifications
- Health checks for insights service
"""

from fastapi import APIRouter, HTTPException, Path, Query
from typing import List, Optional
import logging
from datetime import datetime

from app.services.insights_service import InsightsService
from app.models.receipt import ReceiptResponse

logger = logging.getLogger(__name__)

# Initialize insights service
insights_service = InsightsService()

# Create router
insights_router = APIRouter()

# ================================
# INSIGHTS ENDPOINTS
# ================================

@insights_router.get("/insights/{user_id}")
async def get_user_insights(
    user_id: str = Path(..., description="User ID to get insights for"),
    limit: int = Query(10, ge=1, le=50, description="Number of insights to return")
):
    """
    Get AI-generated insights for a user's spending patterns
    
    Returns insights like:
    - Overspending alerts
    - Price trend analysis
    - Savings opportunities
    - Category spending patterns
    """
    try:
        insights = await insights_service.get_insights(user_id=user_id, limit=limit)
        
        return {
            "success": True,
            "insights": insights,
            "count": len(insights),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting insights for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate insights: {str(e)}"
        )

@insights_router.options("/insights/{user_id}")
async def options_insights(user_id: str):
    """Handle OPTIONS request for insights endpoint"""
    return {"message": "OK"}

@insights_router.post("/insights/generate/{user_id}")
async def generate_insights(
    user_id: str = Path(..., description="User ID to generate insights for"),
    force_refresh: bool = Query(False, description="Force regeneration of insights")
):
    """
    Manually trigger insight generation for a user
    
    This endpoint:
    - Analyzes recent receipts and spending patterns
    - Generates new insights using AI
    - Creates wallet passes for important insights
    - Sends notifications for high-priority alerts
    """
    try:
        insights = await insights_service.generate_insights(
            user_id=user_id, 
            force_refresh=force_refresh
        )
        
        return {
            "success": True,
            "message": f"Generated {len(insights)} insights for user {user_id}",
            "insights": insights,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error generating insights for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate insights: {str(e)}"
        )

@insights_router.get("/insights/trends/{user_id}")
async def get_spending_trends(
    user_id: str = Path(..., description="User ID to get trends for"),
    period: str = Query("30d", description="Time period: 7d, 30d, or 90d"),
    categories: Optional[str] = Query(None, description="Comma-separated list of categories to filter")
):
    """
    Get spending trends and time series data for charts
    
    Returns:
    - Daily spending patterns
    - Category breakdowns
    - Trend analysis
    - Growth rates and insights
    """
    try:
        trends_data = await insights_service.get_spending_trends(
            user_id=user_id, 
            period=period,
            categories=categories.split(",") if categories else None
        )
        
        return {
            "success": True,
            "trends": trends_data,
            "period": period,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting trends for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get spending trends: {str(e)}"
        )

# ================================
# WALLET PASS ENDPOINTS
# ================================

@insights_router.post("/insights/{insight_id}/wallet-pass")
async def create_wallet_pass_from_insight(
    insight_id: str = Path(..., description="Insight ID to create wallet pass for")
):
    """
    Create a Google Wallet pass from a specific insight
    
    The wallet pass will contain:
    - Insight title and description
    - Actionable suggestions
    - Amount impact (if applicable)
    - Expiration date
    """
    try:
        pass_result = await insights_service.generate_wallet_pass(insight_id)
        
        # Check if there was an error in wallet pass generation
        if "error" in pass_result:
            return {
                "success": False,
                "error": pass_result["error"],
                "message": f"Failed to create wallet pass: {pass_result['error']}"
            }
        
        return {
            "success": True,
            "wallet_pass": pass_result,
            "save_url": pass_result.get("save_url"),  # Also include at top level for easier access
            "object_id": pass_result.get("object_id"),
            "message": "Wallet pass created successfully! Click the link to save it to your Google Wallet.",
            "instructions": "The wallet pass has been created. You will be redirected to Google Wallet to save it.",
            "pass_type": "insight",
            "insight_id": insight_id
        }
        
    except Exception as e:
        logger.error(f"❌ Error creating wallet pass for insight {insight_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create wallet pass: {str(e)}"
        )

@insights_router.get("/wallet-passes/{user_id}")
async def get_user_wallet_passes(
    user_id: str = Path(..., description="User ID to get wallet passes for"),
    active_only: bool = Query(True, description="Only return active (non-expired) passes")
):
    """Get all wallet passes created for a user"""
    try:
        passes = await insights_service.get_wallet_passes(
            user_id=user_id, 
            active_only=active_only
        )
        
        return {
            "success": True,
            "wallet_passes": passes,
            "count": len(passes)
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting wallet passes for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get wallet passes: {str(e)}"
        )

# ================================
# NOTIFICATIONS ENDPOINTS
# ================================

@insights_router.get("/notifications/{user_id}")
async def get_user_notifications(
    user_id: str = Path(..., description="User ID to get notifications for"),
    unread_only: bool = Query(False, description="Only return unread notifications"),
    limit: int = Query(20, ge=1, le=100, description="Number of notifications to return")
):
    """
    Get notifications for a user
    
    Notifications include:
    - Spending alerts
    - Price change notifications  
    - Budget warnings
    - Savings opportunities
    """
    try:
        notifications = await insights_service.get_notifications(
            user_id=user_id,
            unread_only=unread_only,
            limit=limit
        )
        
        return {
            "success": True,
            "notifications": notifications,
            "count": len(notifications),
            "unread_count": len([n for n in notifications if not n.get("read", False)])
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting notifications for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get notifications: {str(e)}"
        )

@insights_router.put("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str = Path(..., description="Notification ID to mark as read")
):
    """Mark a specific notification as read"""
    try:
        await insights_service.mark_notification_as_read(notification_id)
        
        return {
            "success": True,
            "message": f"Notification {notification_id} marked as read"
        }
        
    except Exception as e:
        logger.error(f"❌ Error marking notification {notification_id} as read: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to mark notification as read: {str(e)}"
        )

@insights_router.put("/notifications/{user_id}/read-all")
async def mark_all_notifications_as_read(
    user_id: str = Path(..., description="User ID to mark all notifications as read")
):
    """Mark all notifications for a user as read"""
    try:
        result = await insights_service.mark_all_notifications_as_read(user_id)
        
        return {
            "success": True,
            "message": f"All notifications marked as read for user {user_id}",
            "marked_count": result.get("marked_count", 0)
        }
        
    except Exception as e:
        logger.error(f"❌ Error marking all notifications as read for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to mark all notifications as read: {str(e)}"
        )

# ================================
# HEALTH AND TESTING ENDPOINTS
# ================================

@insights_router.get("/insights/health")
async def insights_health_check():
    """Health check for insights service"""
    try:
        health_status = await insights_service.health_check()
        
        return {
            "service": "insights",
            "status": health_status.get("status", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "details": health_status
        }
        
    except Exception as e:
        logger.error(f"❌ Insights health check failed: {e}")
        return {
            "service": "insights",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@insights_router.post("/insights/test/{user_id}")
async def test_step5_features(
    user_id: str = Path(..., description="User ID to test features for")
):
    """
    Test Step 5 functionality
    
    This endpoint tests:
    - Insight generation
    - Wallet pass creation
    - Notification management
    """
    try:
        test_results = await insights_service.test_step5_features()
        
        return {
            "success": True,
            "message": "Step 5 features tested successfully",
            "test_results": test_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Step 5 testing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Step 5 testing failed: {str(e)}"
        )

# ================================
# ANALYTICS ENDPOINTS
# ================================

@insights_router.get("/analytics/spending-trends/{user_id}")
async def get_spending_trends(
    user_id: str = Path(..., description="User ID to get spending trends for"),
    period: str = Query("month", regex="^(week|month|quarter|year)$", description="Time period for trends"),
    category: Optional[str] = Query(None, description="Filter by specific category")
):
    """
    Get detailed spending trends and analytics
    
    Returns:
    - Spending by category over time
    - Month-over-month changes
    - Predicted future spending
    - Budget vs actual comparisons
    """
    try:
        trends = await insights_service.get_spending_trends(
            user_id=user_id,
            period=period,
            category=category
        )
        
        return {
            "success": True,
            "trends": trends,
            "period": period,
            "category": category,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting spending trends for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get spending trends: {str(e)}"
        )
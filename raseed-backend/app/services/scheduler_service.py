# app/services/scheduler_service.py
"""
Step 5: Scheduler Service for Automated Insights
===============================================

This service handles:
1. Scheduled insight generation (daily, weekly, monthly)
2. Background job management
3. Automated notification triggers
4. Wallet pass updates
5. System health monitoring
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
import json
from enum import Enum
import threading
import time
from google.cloud import firestore

# Core dependencies
from app.core.config import settings
from app.core.database import db
from app.services.insights_service import insights_service, InsightType, AlertPriority
from app.services.wallet_service import WalletService
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    """Status of scheduled jobs"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobFrequency(Enum):
    """Frequency of scheduled jobs"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    HOURLY = "hourly"
    CUSTOM = "custom"

@dataclass
class ScheduledJob:
    """Data structure for scheduled jobs"""
    job_id: str
    name: str
    frequency: JobFrequency
    next_run: datetime
    last_run: Optional[datetime]
    status: JobStatus
    function: Callable
    parameters: Dict
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class SchedulerService:
    """Service for managing scheduled jobs and automated insights"""
    
    def __init__(self):
        self.db = db
        self.wallet_service = WalletService()
        self.jobs: Dict[str, ScheduledJob] = {}
        self.is_running = False
        self.scheduler_thread = None
        
        # Initialize default jobs
        self._setup_default_jobs()
        
        logger.info("✅ Scheduler service initialized")

    def _setup_default_jobs(self):
        """Setup default scheduled jobs"""
        try:
            # Daily insights generation (runs every day at 9 AM)
            daily_insights_job = ScheduledJob(
                job_id="daily_insights",
                name="Daily Insights Generation",
                frequency=JobFrequency.DAILY,
                next_run=self._get_next_daily_run(hour=9),
                last_run=None,
                status=JobStatus.PENDING,
                function=self._run_daily_insights,
                parameters={}
            )
            self.jobs[daily_insights_job.job_id] = daily_insights_job
            
            # Weekly spending analysis (runs every Monday at 10 AM)
            weekly_analysis_job = ScheduledJob(
                job_id="weekly_analysis",
                name="Weekly Spending Analysis",
                frequency=JobFrequency.WEEKLY,
                next_run=self._get_next_weekly_run(weekday=0, hour=10),  # Monday = 0
                last_run=None,
                status=JobStatus.PENDING,
                function=self._run_weekly_analysis,
                parameters={}
            )
            self.jobs[weekly_analysis_job.job_id] = weekly_analysis_job
            
            # Monthly budget review (runs on 1st of each month at 8 AM)
            monthly_budget_job = ScheduledJob(
                job_id="monthly_budget",
                name="Monthly Budget Review",
                frequency=JobFrequency.MONTHLY,
                next_run=self._get_next_monthly_run(day=1, hour=8),
                last_run=None,
                status=JobStatus.PENDING,
                function=self._run_monthly_budget_review,
                parameters={}
            )
            self.jobs[monthly_budget_job.job_id] = monthly_budget_job
            
            # Price trend monitoring (runs every 6 hours)
            price_monitoring_job = ScheduledJob(
                job_id="price_monitoring",
                name="Price Trend Monitoring",
                frequency=JobFrequency.CUSTOM,
                next_run=datetime.now() + timedelta(hours=6),
                last_run=None,
                status=JobStatus.PENDING,
                function=self._run_price_monitoring,
                parameters={"interval_hours": 6}
            )
            self.jobs[price_monitoring_job.job_id] = price_monitoring_job
            
            # Wallet pass updates (runs every 2 hours)
            wallet_update_job = ScheduledJob(
                job_id="wallet_updates",
                name="Wallet Pass Updates",
                frequency=JobFrequency.CUSTOM,
                next_run=datetime.now() + timedelta(hours=2),
                last_run=None,
                status=JobStatus.PENDING,
                function=self._run_wallet_updates,
                parameters={"interval_hours": 2}
            )
            self.jobs[wallet_update_job.job_id] = wallet_update_job
            
            logger.info(f"📅 Setup {len(self.jobs)} default scheduled jobs")
            
        except Exception as e:
            logger.error(f"❌ Error setting up default jobs: {e}")

    # ============================================================================
    # SCHEDULER MANAGEMENT
    # ============================================================================

    def start_scheduler(self):
        """Start the background scheduler"""
        if self.is_running:
            logger.warning("⚠️ Scheduler is already running")
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("🚀 Scheduler started successfully")

    def stop_scheduler(self):
        """Stop the background scheduler"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("🛑 Scheduler stopped")

    def _run_scheduler(self):
        """Main scheduler loop"""
        logger.info("🔄 Scheduler loop started")
        
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # Check each job to see if it needs to run
                for job_id, job in self.jobs.items():
                    if job.status == JobStatus.PENDING and current_time >= job.next_run:
                        asyncio.create_task(self._execute_job(job))
                
                # Sleep for 60 seconds before checking again
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"❌ Error in scheduler loop: {e}")
                time.sleep(60)  # Continue running even if there's an error

    async def _execute_job(self, job: ScheduledJob):
        """Execute a scheduled job"""
        logger.info(f"🏃‍♂️ Executing job: {job.name}")
        
        try:
            # Update job status
            job.status = JobStatus.RUNNING
            job.last_run = datetime.now()
            
            # Execute the job function
            if asyncio.iscoroutinefunction(job.function):
                result = await job.function(**job.parameters)
            else:
                result = job.function(**job.parameters)
            
            # Job completed successfully
            job.status = JobStatus.COMPLETED
            job.retry_count = 0
            job.next_run = self._calculate_next_run(job)
            
            # Log the result
            await self._log_job_execution(job, result, success=True)
            
            logger.info(f"✅ Job completed: {job.name}")
            
        except Exception as e:
            logger.error(f"❌ Job failed: {job.name} - {e}")
            
            # Handle job failure
            job.retry_count += 1
            if job.retry_count <= job.max_retries:
                # Retry after 5 minutes
                job.status = JobStatus.PENDING
                job.next_run = datetime.now() + timedelta(minutes=5)
                logger.info(f"🔄 Retrying job {job.name} (attempt {job.retry_count}/{job.max_retries})")
            else:
                # Max retries reached
                job.status = JobStatus.FAILED
                job.next_run = self._calculate_next_run(job)  # Schedule for next regular interval
                logger.error(f"💥 Job permanently failed: {job.name}")
            
            await self._log_job_execution(job, str(e), success=False)

    # ============================================================================
    # JOB IMPLEMENTATIONS
    # ============================================================================

    async def _run_daily_insights(self) -> Dict:
        """Daily insights generation for all users"""
        logger.info("📊 Running daily insights generation")
        
        try:
            # Get all users who have uploaded receipts in the last 7 days
            cutoff_date = datetime.now() - timedelta(days=7)
            
            # Query active users
            receipts_ref = self.db.collection('receipts').where('upload_date', '>=', cutoff_date)
            recent_receipts = receipts_ref.stream()
            
            active_users = set()
            for receipt in recent_receipts:
                receipt_data = receipt.to_dict()
                user_id = receipt_data.get('user_id')
                if user_id:
                    active_users.add(user_id)
            
            logger.info(f"🎯 Found {len(active_users)} active users for daily analysis")
            
            total_insights = 0
            processed_users = 0
            
            # Generate insights for each active user
            for user_id in active_users:
                try:
                    insights = await insights_service.generate_proactive_insights(user_id)
                    total_insights += len(insights)
                    processed_users += 1
                    
                    # Small delay to avoid overwhelming the system
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"❌ Failed to generate insights for user {user_id}: {e}")
            
            result = {
                'job': 'daily_insights',
                'status': 'completed',
                'users_processed': processed_users,
                'total_insights_generated': total_insights,
                'execution_time': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Daily insights completed: {total_insights} insights for {processed_users} users")
            return result
            
        except Exception as e:
            logger.error(f"❌ Daily insights job failed: {e}")
            raise

    async def _run_weekly_analysis(self) -> Dict:
        """Weekly spending analysis and trend detection"""
        logger.info("📈 Running weekly spending analysis")
        
        try:
            # Get all users
            users_ref = self.db.collection('users')
            users = users_ref.stream()
            
            processed_users = 0
            total_trends = 0
            
            for user in users:
                user_data = user.to_dict()
                user_id = user.id
                
                try:
                    # Generate spending trends
                    trends = await insights_service.get_spending_trends(user_id)
                    total_trends += len(trends)
                    
                    # Create weekly summary insights
                    if trends:
                        weekly_summary = await self._create_weekly_summary(user_id, trends)
                        if weekly_summary:
                            await insights_service._save_insights([weekly_summary])
                    
                    processed_users += 1
                    
                except Exception as e:
                    logger.error(f"❌ Weekly analysis failed for user {user_id}: {e}")
            
            result = {
                'job': 'weekly_analysis',
                'status': 'completed',
                'users_processed': processed_users,
                'trends_analyzed': total_trends,
                'execution_time': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Weekly analysis completed: {total_trends} trends for {processed_users} users")
            return result
            
        except Exception as e:
            logger.error(f"❌ Weekly analysis job failed: {e}")
            raise

    async def _run_monthly_budget_review(self) -> Dict:
        """Monthly budget review and forecasting"""
        logger.info("💰 Running monthly budget review")
        
        try:
            # Get all users with receipts in the last month
            cutoff_date = datetime.now() - timedelta(days=30)
            
            receipts_ref = self.db.collection('receipts').where('upload_date', '>=', cutoff_date)
            recent_receipts = receipts_ref.stream()
            
            users_spending = {}
            for receipt in recent_receipts:
                receipt_data = receipt.to_dict()
                user_id = receipt_data.get('user_id')
                total = float(receipt_data.get('extracted_data', {}).get('total', 0))
                
                if user_id:
                    if user_id not in users_spending:
                        users_spending[user_id] = []
                    users_spending[user_id].append(total)
            
            processed_users = 0
            budget_insights = 0
            
            for user_id, spending_amounts in users_spending.items():
                try:
                    monthly_total = sum(spending_amounts)
                    avg_transaction = monthly_total / len(spending_amounts) if spending_amounts else 0
                    
                    # Create monthly budget insight
                    budget_insight = await self._create_budget_insight(user_id, monthly_total, avg_transaction)
                    if budget_insight:
                        await insights_service._save_insights([budget_insight])
                        budget_insights += 1
                    
                    processed_users += 1
                    
                except Exception as e:
                    logger.error(f"❌ Budget review failed for user {user_id}: {e}")
            
            result = {
                'job': 'monthly_budget',
                'status': 'completed',
                'users_processed': processed_users,
                'budget_insights_created': budget_insights,
                'execution_time': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Monthly budget review completed: {budget_insights} insights for {processed_users} users")
            return result
            
        except Exception as e:
            logger.error(f"❌ Monthly budget review job failed: {e}")
            raise

    async def _run_price_monitoring(self, interval_hours: int = 6) -> Dict:
        """Monitor price trends and alert on significant changes"""
        logger.info(f"💲 Running price monitoring (interval: {interval_hours}h)")
        
        try:
            # Get all users
            users_ref = self.db.collection('users')
            users = users_ref.stream()
            
            processed_users = 0
            price_alerts = 0
            
            for user in users:
                user_id = user.id
                
                try:
                    # Get recent receipts for price analysis
                    receipts = await insights_service._get_user_receipts(user_id, days_back=30)
                    
                    if receipts:
                        # Analyze price trends
                        price_insights = await insights_service._analyze_price_trends(user_id, receipts)
                        
                        if price_insights:
                            await insights_service._save_insights(price_insights)
                            price_alerts += len(price_insights)
                    
                    processed_users += 1
                    
                except Exception as e:
                    logger.error(f"❌ Price monitoring failed for user {user_id}: {e}")
            
            # Schedule next run
            next_job = self.jobs.get('price_monitoring')
            if next_job:
                next_job.next_run = datetime.now() + timedelta(hours=interval_hours)
            
            result = {
                'job': 'price_monitoring',
                'status': 'completed',
                'users_processed': processed_users,
                'price_alerts_generated': price_alerts,
                'next_run': (datetime.now() + timedelta(hours=interval_hours)).isoformat(),
                'execution_time': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Price monitoring completed: {price_alerts} alerts for {processed_users} users")
            return result
            
        except Exception as e:
            logger.error(f"❌ Price monitoring job failed: {e}")
            raise

    async def _run_wallet_updates(self, interval_hours: int = 2) -> Dict:
        """Update wallet passes with new insights and data"""
        logger.info(f"🎫 Running wallet pass updates (interval: {interval_hours}h)")
        
        try:
            # Get insights that need wallet pass updates
            cutoff_time = datetime.now() - timedelta(hours=interval_hours)
            
            insights_ref = (self.db.collection('insights')
                          .where('created_at', '>=', cutoff_time)
                          .where('wallet_pass_eligible', '==', True))
            
            recent_insights = insights_ref.stream()
            
            updated_passes = 0
            processed_insights = 0
            
            for insight_doc in recent_insights:
                try:
                    insight_data = insight_doc.to_dict()
                    user_id = insight_data.get('user_id')
                    
                    if user_id:
                        # Create or update wallet pass
                        pass_url = await self.wallet_service.create_insights_pass(
                            user_id=user_id,
                            insight_data=insight_data
                        )
                        
                        if pass_url:
                            updated_passes += 1
                    
                    processed_insights += 1
                    
                except Exception as e:
                    logger.error(f"❌ Wallet update failed for insight {insight_doc.id}: {e}")
            
            # Schedule next run
            next_job = self.jobs.get('wallet_updates')
            if next_job:
                next_job.next_run = datetime.now() + timedelta(hours=interval_hours)
            
            result = {
                'job': 'wallet_updates',
                'status': 'completed',
                'insights_processed': processed_insights,
                'passes_updated': updated_passes,
                'next_run': (datetime.now() + timedelta(hours=interval_hours)).isoformat(),
                'execution_time': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Wallet updates completed: {updated_passes} passes updated from {processed_insights} insights")
            return result
            
        except Exception as e:
            logger.error(f"❌ Wallet updates job failed: {e}")
            raise

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    async def _create_weekly_summary(self, user_id: str, trends: List) -> Optional[dict]:
        """Create a weekly spending summary insight"""
        try:
            from app.services.insights_service import SpendingInsight
            
            total_spending = sum(trend.current_period_total for trend in trends)
            increasing_categories = [t for t in trends if t.trend_direction == "increasing"]
            
            summary = SpendingInsight(
                insight_id=f"weekly_summary_{user_id}_{datetime.now().strftime('%Y_%W')}",
                user_id=user_id,
                insight_type=InsightType.CATEGORY_ANALYSIS,
                priority=AlertPriority.LOW,
                title="📊 Weekly Spending Summary",
                description=f"This week you spent ₹{total_spending:,.0f} across {len(trends)} categories.",
                amount_impact=total_spending,
                time_period="week",
                actionable_suggestions=[
                    "Review categories with increasing spending",
                    "Set spending goals for the upcoming week",
                    "Look for opportunities to save on frequent purchases"
                ],
                supporting_data={
                    'trends': [
                        {
                            'category': t.category,
                            'current_total': t.current_period_total,
                            'trend': t.trend_direction,
                            'change': t.percentage_change
                        } for t in trends
                    ],
                    'increasing_categories': len(increasing_categories)
                },
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=7)
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error creating weekly summary: {e}")
            return None

    async def _create_budget_insight(self, user_id: str, monthly_total: float, avg_transaction: float) -> Optional[Dict]:
        """Create a monthly budget insight"""
        try:
            from app.services.insights_service import SpendingInsight
            
            # Simple budget recommendation based on spending patterns
            recommended_budget = monthly_total * 1.1  # 10% buffer
            
            insight = SpendingInsight(
                insight_id=f"budget_review_{user_id}_{datetime.now().strftime('%Y_%m')}",
                user_id=user_id,
                insight_type=InsightType.BUDGET_ALERT,
                priority=AlertPriority.MEDIUM,
                title="💰 Monthly Budget Review",
                description=f"You spent ₹{monthly_total:,.0f} this month with an average transaction of ₹{avg_transaction:.0f}.",
                amount_impact=monthly_total,
                time_period="month",
                actionable_suggestions=[
                    f"Consider setting a budget of ₹{recommended_budget:,.0f} for next month",
                    "Track daily spending to stay within budget",
                    "Identify your largest expense categories",
                    "Look for subscription services you can optimize"
                ],
                supporting_data={
                    'monthly_total': monthly_total,
                    'average_transaction': avg_transaction,
                    'recommended_budget': recommended_budget,
                    'transaction_count': int(monthly_total / avg_transaction) if avg_transaction > 0 else 0
                },
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=30)
            )
            
            return insight
            
        except Exception as e:
            logger.error(f"❌ Error creating budget insight: {e}")
            return None

    def _calculate_next_run(self, job: ScheduledJob) -> datetime:
        """Calculate the next run time for a job"""
        now = datetime.now()
        
        if job.frequency == JobFrequency.DAILY:
            return self._get_next_daily_run(hour=9)
        elif job.frequency == JobFrequency.WEEKLY:
            return self._get_next_weekly_run(weekday=0, hour=10)
        elif job.frequency == JobFrequency.MONTHLY:
            return self._get_next_monthly_run(day=1, hour=8)
        elif job.frequency == JobFrequency.HOURLY:
            return now + timedelta(hours=1)
        elif job.frequency == JobFrequency.CUSTOM:
            interval_hours = job.parameters.get('interval_hours', 24)
            return now + timedelta(hours=interval_hours)
        else:
            return now + timedelta(days=1)  # Default to daily

    def _get_next_daily_run(self, hour: int = 9) -> datetime:
        """Get next daily run time"""
        now = datetime.now()
        next_run = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        if next_run <= now:
            next_run += timedelta(days=1)
        
        return next_run

    def _get_next_weekly_run(self, weekday: int = 0, hour: int = 10) -> datetime:
        """Get next weekly run time (weekday: 0=Monday, 6=Sunday)"""
        now = datetime.now()
        days_ahead = weekday - now.weekday()
        
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        next_run = now + timedelta(days=days_ahead)
        next_run = next_run.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        return next_run

    def _get_next_monthly_run(self, day: int = 1, hour: int = 8) -> datetime:
        """Get next monthly run time"""
        now = datetime.now()
        
        if now.day < day:
            # This month
            next_run = now.replace(day=day, hour=hour, minute=0, second=0, microsecond=0)
        else:
            # Next month
            if now.month == 12:
                next_run = now.replace(year=now.year+1, month=1, day=day, hour=hour, minute=0, second=0, microsecond=0)
            else:
                next_run = now.replace(month=now.month+1, day=day, hour=hour, minute=0, second=0, microsecond=0)
        
        return next_run

    async def _log_job_execution(self, job: ScheduledJob, result: any, success: bool):
        """Log job execution results"""
        try:
            log_data = {
                'job_id': job.job_id,
                'job_name': job.name,
                'execution_time': datetime.now(),
                'success': success,
                'result': result if success else None,
                'error': result if not success else None,
                'retry_count': job.retry_count,
                'next_run': job.next_run
            }
            
            # Save to Firestore
            await self.db.collection('job_logs').add(log_data)
            
        except Exception as e:
            logger.error(f"❌ Error logging job execution: {e}")

    # ============================================================================
    # PUBLIC API METHODS
    # ============================================================================

    def get_job_status(self, job_id: str = None) -> Dict:
        """Get status of all jobs or a specific job"""
        if job_id:
            job = self.jobs.get(job_id)
            if job:
                return {
                    'job_id': job.job_id,
                    'name': job.name,
                    'status': job.status.value,
                    'frequency': job.frequency.value,
                    'next_run': job.next_run.isoformat(),
                    'last_run': job.last_run.isoformat() if job.last_run else None,
                    'retry_count': job.retry_count,
                    'max_retries': job.max_retries
                }
            else:
                return {'error': f'Job {job_id} not found'}
        else:
            return {
                'scheduler_running': self.is_running,
                'total_jobs': len(self.jobs),
                'jobs': [
                    {
                        'job_id': job.job_id,
                        'name': job.name,
                        'status': job.status.value,
                        'next_run': job.next_run.isoformat(),
                        'last_run': job.last_run.isoformat() if job.last_run else None
                    } for job in self.jobs.values()
                ]
            }

    async def trigger_job_manually(self, job_id: str) -> Dict:
        """Manually trigger a specific job"""
        job = self.jobs.get(job_id)
        if not job:
            return {'error': f'Job {job_id} not found'}
        
        try:
            logger.info(f"🚀 Manually triggering job: {job.name}")
            await self._execute_job(job)
            
            return {
                'status': 'success',
                'message': f'Job {job.name} triggered successfully',
                'job_id': job_id,
                'execution_time': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ Error manually triggering job {job_id}: {e}")
            return {
                'status': 'error',
                'message': f'Failed to trigger job {job.name}',
                'error': str(e)
            }

    def add_custom_job(self, job_config: Dict) -> Dict:
        """Add a custom scheduled job"""
        try:
            # Validate job configuration
            required_fields = ['job_id', 'name', 'frequency', 'function']
            for field in required_fields:
                if field not in job_config:
                    return {'error': f'Missing required field: {field}'}
            
            # Check if job_id already exists
            if job_config['job_id'] in self.jobs:
                return {'error': f'Job with ID {job_config["job_id"]} already exists'}
            
            # Create new job
            new_job = ScheduledJob(
                job_id=job_config['job_id'],
                name=job_config['name'],
                frequency=JobFrequency(job_config['frequency']),
                next_run=datetime.now() + timedelta(minutes=5),  # Start in 5 minutes
                last_run=None,
                status=JobStatus.PENDING,
                function=job_config['function'],
                parameters=job_config.get('parameters', {}),
                max_retries=job_config.get('max_retries', 3)
            )
            
            self.jobs[new_job.job_id] = new_job
            
            logger.info(f"✅ Added custom job: {new_job.name}")
            
            return {
                'status': 'success',
                'message': f'Custom job {new_job.name} added successfully',
                'job_id': new_job.job_id,
                'next_run': new_job.next_run.isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ Error adding custom job: {e}")
            return {
                'status': 'error',
                'message': 'Failed to add custom job',
                'error': str(e)
            }

    def remove_job(self, job_id: str) -> Dict:
        """Remove a scheduled job"""
        if job_id not in self.jobs:
            return {'error': f'Job {job_id} not found'}
        
        job = self.jobs[job_id]
        del self.jobs[job_id]
        
        logger.info(f"🗑️ Removed job: {job.name}")
        
        return {
            'status': 'success',
            'message': f'Job {job.name} removed successfully',
            'job_id': job_id
        }

    async def get_job_logs(self, job_id: str = None, limit: int = 50) -> List[Dict]:
        """Get execution logs for jobs"""
        try:
            query = self.db.collection('job_logs')
            
            if job_id:
                query = query.where('job_id', '==', job_id)
            
            query = query.order_by('execution_time', direction=firestore.Query.DESCENDING).limit(limit)
            
            logs = query.stream()
            return [log.to_dict() for log in logs]
        
        except Exception as e:
            logger.error(f"❌ Error getting job logs: {e}")
            return []

    def get_scheduler_health(self) -> Dict:
        """Get scheduler health and performance metrics"""
        try:
            total_jobs = len(self.jobs)
            running_jobs = len([j for j in self.jobs.values() if j.status == JobStatus.RUNNING])
            failed_jobs = len([j for j in self.jobs.values() if j.status == JobStatus.FAILED])
            pending_jobs = len([j for j in self.jobs.values() if j.status == JobStatus.PENDING])
            
            # Calculate uptime
            uptime_seconds = 0
            if hasattr(self, 'start_time'):
                uptime_seconds = (datetime.now() - self.start_time).total_seconds()
            
            return {
                'scheduler_status': 'running' if self.is_running else 'stopped',
                'uptime_seconds': uptime_seconds,
                'total_jobs': total_jobs,
                'job_status_breakdown': {
                    'running': running_jobs,
                    'pending': pending_jobs,
                    'failed': failed_jobs,
                    'completed': total_jobs - running_jobs - failed_jobs - pending_jobs
                },
                'next_job_run': min([j.next_run for j in self.jobs.values()]).isoformat() if self.jobs else None,
                'health_score': max(0, 100 - (failed_jobs * 20)),  # Simple health score
                'last_check': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ Error getting scheduler health: {e}")
            return {
                'scheduler_status': 'error',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }

# Create global instance
scheduler_service = SchedulerService()
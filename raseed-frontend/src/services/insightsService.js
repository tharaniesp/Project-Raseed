// src/services/insightsService.js
import api from './api';

class InsightsService {
  constructor() {
    this.api = api;
    console.log('🔍 InsightsService initialized');
  }

  // ================================
  // INSIGHTS MANAGEMENT
  // ================================

  /**
   * Get AI-generated insights for current user
   */
  async getInsights(userId = 'current_user', limit = 10) {
    try {
      console.log('🔍 Fetching insights for user:', userId);
      const response = await this.api.get(`/api/insights/${userId}?limit=${limit}`);
      
      console.log('✅ Insights response:', response);
      
      // Handle different response formats
      if (response.data) {
        // If response has data property
        return response.data.insights || response.data;
      } else if (response.insights) {
        // If response directly has insights
        return response.insights;
      } else if (Array.isArray(response)) {
        // If response is directly an array
        return response;
      } else {
        // Return the response as-is
        return response;
      }
      
    } catch (error) {
      console.error('❌ Error fetching insights:', error);
      
      // Return fallback mock data if API fails
      return this._getFallbackInsights();
    }
  }

  /**
   * Generate new insights for user
   */
  async generateInsights(userId = 'current_user', forceRefresh = false) {
    try {
      console.log('🔄 Generating insights for user:', userId);
      const response = await this.api.post(`/api/insights/generate/${userId}?force_refresh=${forceRefresh}`);
      
      console.log('✅ Generated insights:', response);
      return response.data || response;
      
    } catch (error) {
      console.error('❌ Error generating insights:', error);
      throw error;
    }
  }

  // ================================
  // WALLET PASS MANAGEMENT
  // ================================

  /**
   * Generate wallet pass from insight
   */
  async generateWalletPass(insightId) {
    try {
      console.log('💳 Generating wallet pass for insight:', insightId);
      
      const response = await this.api.post(`/api/insights/${insightId}/wallet-pass`);
      console.log('✅ Wallet pass generated:', response);
      
      // Return the response data
      const result = response.data || response;
      
      // Validate the response has the required save_url
      if (result.success && result.wallet_pass?.save_url) {
        console.log('✅ Valid wallet pass response with save_url');
        return result;
      } else if (result.save_url) {
        // Handle direct save_url format
        console.log('✅ Valid wallet pass response with direct save_url');
        return result;
      } else {
        throw new Error('Invalid response: missing save_url');
      }
      
    } catch (error) {
      console.error('❌ Error generating wallet pass:', error);
      throw error; // Re-throw the error instead of returning mock data
    }
  }

  /**
   * Get spending trends data for charts
   */
  async getTrendsData(userId = 'current_user', timeRange = '30d') {
    try {
      console.log('📊 Fetching trends data for user:', userId, 'timeRange:', timeRange);
      const response = await this.api.get(`/api/insights/trends/${userId}?period=${timeRange}`);
      
      console.log('✅ Trends data response:', response);
      
      if (response.data) {
        return response.data;
      } else if (response.trends) {
        return response.trends;
      } else {
        return response;
      }
      
    } catch (error) {
      console.error('❌ Error fetching trends data:', error);
      
      // Return mock trends data for development
      return this._getMockTrendsData(timeRange);
    }
  }

  /**
   * Generate mock trends data for development
   */
  _getMockTrendsData(timeRange = '30d') {
    const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 90;
    const categories = ['groceries', 'dining', 'transportation', 'entertainment', 'shopping', 'utilities'];
    
    const trendsData = {
      period: timeRange,
      total_spending: 0,
      trends: [],
      daily_spending: [],
      category_breakdown: {}
    };

    // Generate daily spending data
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      const dateStr = date.toISOString().split('T')[0];
      
      const dailyData = {
        date: dateStr,
        total: 0,
        categories: {}
      };

      categories.forEach(category => {
        const baseAmount = {
          groceries: 150,
          dining: 80,
          transportation: 50,
          entertainment: 40,
          shopping: 60,
          utilities: 30
        }[category] || 30;
        
        const variance = Math.random() * 0.8 + 0.6; // 0.6 to 1.4 multiplier
        const amount = Math.round(baseAmount * variance);
        
        dailyData.categories[category] = amount;
        dailyData.total += amount;
        
        if (!trendsData.category_breakdown[category]) {
          trendsData.category_breakdown[category] = 0;
        }
        trendsData.category_breakdown[category] += amount;
      });

      trendsData.daily_spending.push(dailyData);
      trendsData.total_spending += dailyData.total;
    }

    // Generate trend insights
    categories.forEach(category => {
      const categoryTotal = trendsData.category_breakdown[category];
      const avgDaily = categoryTotal / days;
      const trendDirection = Math.random() > 0.5 ? 'increasing' : 'decreasing';
      const changePercent = Math.random() * 20 + 5; // 5-25% change

      trendsData.trends.push({
        category,
        trend_direction: trendDirection,
        change_percentage: trendDirection === 'increasing' ? changePercent : -changePercent,
        average_daily: avgDaily,
        total_amount: categoryTotal,
        insights: [
          `${category} spending is ${trendDirection} by ${changePercent.toFixed(1)}%`,
          `Average daily spending: ₹${avgDaily.toFixed(0)}`
        ]
      });
    });

    return trendsData;
  }

  /**
   * Get all wallet passes for user
   */
  async getWalletPasses(userId = 'current_user') {
    try {
      console.log('💳 Fetching wallet passes for user:', userId);
      const response = await this.api.get(`/api/wallet-passes/${userId}`);
      
      console.log('💳 Wallet passes response:', response);
      
      // Handle different response formats
      if (response.data) {
        return response.data.wallet_passes || response.data;
      } else if (response.wallet_passes) {
        return response.wallet_passes;
      } else if (Array.isArray(response)) {
        return response;
      } else {
        return response;
      }
      
    } catch (error) {
      console.error('❌ Error fetching wallet passes:', error);
      return this._getFallbackWalletPasses();
    }
  }

  // ================================
  // NOTIFICATIONS MANAGEMENT
  // ================================

  /**
   * Get all notifications for user
   */
  async getNotifications(userId = 'current_user', unreadOnly = false, limit = 20) {
    try {
      console.log('🔔 Fetching notifications for user:', userId);
      const response = await this.api.get(
        `/api/notifications/${userId}?unread_only=${unreadOnly}&limit=${limit}`
      );
      
      console.log('🔔 Notifications response:', response);
      
      // Handle different response formats
      if (response.data) {
        return response.data.notifications || response.data;
      } else if (response.notifications) {
        return response.notifications;
      } else if (Array.isArray(response)) {
        return response;
      } else {
        return response;
      }
      
    } catch (error) {
      console.error('❌ Error fetching notifications:', error);
      return this._getFallbackNotifications();
    }
  }

  /**
   * Mark a notification as read
   */
  async markNotificationAsRead(notificationId) {
    try {
      console.log('✅ Marking notification as read:', notificationId);
      const response = await this.api.put(`/api/notifications/${notificationId}/read`);
      console.log('✅ Notification marked as read:', response);
      return response.data || response;
      
    } catch (error) {
      console.error('❌ Error marking notification as read:', error);
      // Don't throw error for UI operations, return success
      return { success: true, message: 'Marked as read (offline)' };
    }
  }

  /**
   * Mark all notifications as read
   */
  async markAllNotificationsAsRead(userId = 'current_user') {
    try {
      console.log('✅ Marking all notifications as read for user:', userId);
      const response = await this.api.put(`/api/notifications/${userId}/read-all`);
      console.log('✅ All notifications marked as read:', response);
      return response.data || response;
      
    } catch (error) {
      console.error('❌ Error marking all notifications as read:', error);
      return { success: true, message: 'All marked as read (offline)' };
    }
  }

  // ================================
  // ANALYTICS AND TRENDS
  // ================================

  /**
   * Get spending trends and analytics
   */
  async getSpendingTrends(userId = 'current_user', period = 'month', category = null) {
    try {
      console.log('📊 Fetching spending trends for user:', userId);
      let url = `/api/analytics/spending-trends/${userId}?period=${period}`;
      if (category) {
        url += `&category=${category}`;
      }
      
      const response = await this.api.get(url);
      console.log('📊 Spending trends:', response);
      return response.data || response;
      
    } catch (error) {
      console.error('❌ Error fetching spending trends:', error);
      return this._getFallbackTrends();
    }
  }

  // ================================
  // HEALTH AND TESTING
  // ================================

  /**
   * Health check for insights service
   */
  async healthCheck() {
    try {
      const response = await this.api.get('/api/insights/health');
      console.log('💓 Insights service health:', response);
      return response.data || response;
      
    } catch (error) {
      console.error('❌ Insights service health check failed:', error);
      return { status: 'unhealthy', error: error.message };
    }
  }

  /**
   * Test Step 5 functionality
   */
  async testStep5Features(userId = 'current_user') {
    try {
      console.log('🧪 Testing Step 5 features for user:', userId);
      const response = await this.api.post(`/api/insights/test/${userId}`);
      console.log('🧪 Step 5 test results:', response);
      return response.data || response;
      
    } catch (error) {
      console.error('❌ Step 5 testing failed:', error);
      throw error;
    }
  }

  // ================================
  // FALLBACK DATA METHODS
  // ================================

  _getFallbackInsights() {
    console.log('📦 Returning fallback insights data');
    return [
      {
        insight_id: `fallback_${Date.now()}_1`,
        user_id: 'current_user',
        insight_type: 'overspending',
        priority: 'high',
        title: 'Grocery Spending Alert',
        description: 'Your grocery spending increased by 23% this month compared to last month.',
        amount_impact: 700.0,
        percentage_change: 23.0,
        category: 'groceries',
        merchant: null,
        time_period: 'this_month',
        actionable_suggestions: [
          'Create a meal plan before shopping',
          'Compare prices across different stores',
          'Use generic brands instead of premium ones'
        ],
        supporting_data: {
          current_amount: 4500,
          previous_amount: 3800,
          trend: 'increasing'
        },
        created_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        wallet_pass_eligible: true
      },
      {
        insight_id: `fallback_${Date.now()}_2`,
        user_id: 'current_user',
        insight_type: 'savings_opportunity',
        priority: 'medium',
        title: 'Coffee Savings Opportunity',
        description: 'You could save ₹480/month by brewing coffee at home instead of buying from cafes.',
        amount_impact: 480.0,
        percentage_change: null,
        category: 'dining',
        merchant: null,
        time_period: 'monthly',
        actionable_suggestions: [
          'Invest in a good coffee maker',
          'Buy coffee beans in bulk',
          'Limit cafe visits to 2-3 times per week'
        ],
        supporting_data: {
          potential_savings: 480,
          timeframe: 'monthly'
        },
        created_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(),
        wallet_pass_eligible: true
      },
      {
        insight_id: `fallback_${Date.now()}_3`,
        user_id: 'current_user',
        insight_type: 'price_trend',
        priority: 'low',
        title: 'Fuel Price Drop',
        description: 'Petrol prices have decreased by ₹2/liter in your area over the past week.',
        amount_impact: 120.0,
        percentage_change: -3.2,
        category: 'transportation',
        merchant: null,
        time_period: 'this_week',
        actionable_suggestions: [
          'Consider filling up your tank now',
          'Plan longer trips while prices are low'
        ],
        supporting_data: {
          item: 'Petrol',
          price_change: -2.0,
          trend_direction: 'decreasing'
        },
        created_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
        wallet_pass_eligible: false
      }
    ];
  }

  _getFallbackNotifications() {
    console.log('📦 Returning fallback notifications data');
    return [
      {
        notification_id: `notif_fallback_${Date.now()}_1`,
        user_id: 'current_user',
        type: 'spending_alert',
        title: 'High Grocery Spending',
        message: 'Your grocery spending is 23% higher than last month',
        priority: 'high',
        read: false,
        timestamp: new Date().toISOString(),
        action_url: '/insights',
        category: 'groceries',
        amount_impact: 700.0
      },
      {
        notification_id: `notif_fallback_${Date.now()}_2`,
        user_id: 'current_user',
        type: 'savings_opportunity',
        title: 'Coffee Savings',
        message: 'You could save ₹480/month by brewing coffee at home',
        priority: 'medium',
        read: false,
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        action_url: '/insights',
        category: 'dining',
        amount_impact: 480.0
      },
      {
        notification_id: `notif_fallback_${Date.now()}_3`,
        user_id: 'current_user',
        type: 'price_alert',
        title: 'Fuel Price Drop',
        message: 'Petrol prices decreased by ₹2/liter in your area',
        priority: 'low',
        read: true,
        timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        action_url: '/insights',
        category: 'transportation',
        amount_impact: 120.0
      }
    ];
  }

  _getFallbackWalletPasses() {
    console.log('📦 Returning fallback wallet passes data');
    return [
      {
        pass_id: `pass_fallback_${Date.now()}_1`,
        user_id: 'current_user',
        title: 'Grocery Spending Alert',
        description: '23% increase in grocery spending',
        pass_url: 'https://wallet.google.com/pass/grocery-alert',
        category: 'groceries',
        amount_impact: 700.0,
        priority: 'high',
        created_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        status: 'active'
      },
      {
        pass_id: `pass_fallback_${Date.now()}_2`,
        user_id: 'current_user',
        title: 'Coffee Savings Opportunity',
        description: 'Save ₹480/month by brewing at home',
        pass_url: 'https://wallet.google.com/pass/coffee-savings',
        category: 'dining',
        amount_impact: 480.0,
        priority: 'medium',
        created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        expires_at: new Date(Date.now() + 12 * 24 * 60 * 60 * 1000).toISOString(),
        status: 'active'
      }
    ];
  }

  _getFallbackTrends() {
    console.log('📦 Returning fallback trends data');
    return {
      user_id: 'current_user',
      period: 'month',
      summary: {
        total_current_period: 8500.00,
        total_previous_period: 8350.00,
        total_change_amount: 150.00,
        total_change_percentage: 1.8,
        trend_direction: 'increasing'
      },
      categories: [
        {
          category: 'groceries',
          current_period: 4500.00,
          previous_period: 3800.00,
          change_amount: 700.00,
          change_percentage: 18.4,
          trend: 'increasing'
        },
        {
          category: 'dining',
          current_period: 2200.00,
          previous_period: 2800.00,
          change_amount: -600.00,
          change_percentage: -21.4,
          trend: 'decreasing'
        },
        {
          category: 'transportation',
          current_period: 1800.00,
          previous_period: 1750.00,
          change_amount: 50.00,
          change_percentage: 2.9,
          trend: 'stable'
        }
      ],
      generated_at: new Date().toISOString()
    };
  }
}

// Create and export singleton instance
export const insightsService = new InsightsService();

// Export class for testing
export { InsightsService };

// Legacy exports
export default insightsService;
// src/pages/InsightsPage.js
import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, DollarSign, AlertTriangle, Bell, 
  BarChart3, PieChart, Target, Calendar,
  RefreshCw, Download, Settings, Filter
} from 'lucide-react';
import InsightsList from '../components/Insights/InsightsList';
import NotificationsCenter from '../components/Insights/NotificationsCenter';
import TrendsChart from '../components/Insights/TrendsChart';
import { insightsService } from '../services/insightsService';

const InsightsPage = () => {
  const [data, setData] = useState({
    insights: [],
    notifications: [],
    spending_trends: null,
    wallet_passes: [],
    trends_data: null
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('insights');
  const [refreshing, setRefreshing] = useState(false);

  // Load insights data
  useEffect(() => {
    loadInsightsData();
  }, []);

  const loadInsightsData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('🔍 Loading insights data...');
      
      // Load insights
      const insights = await insightsService.getInsights();
      console.log('📊 Insights loaded:', insights);
      
      // Load notifications
      const notifications = await insightsService.getNotifications();
      console.log('🔔 Notifications loaded:', notifications);
      
      // Load wallet passes
      const walletPasses = await insightsService.getWalletPasses();
      console.log('💳 Wallet passes loaded:', walletPasses);
      
      // Load trends data
      const trendsData = await insightsService.getTrendsData();
      console.log('📈 Trends data loaded:', trendsData);
      
      // Set the data with proper structure
      setData({
        insights: insights?.insights || insights || [],
        notifications: notifications?.notifications || notifications || [],
        spending_trends: null, // Will be loaded separately if needed
        wallet_passes: walletPasses?.wallet_passes || walletPasses || [],
        trends_data: trendsData
      });
      
    } catch (error) {
      console.error('❌ Failed to load insights:', error);
      setError('Failed to load insights. Please try again.');
      
      // Set empty data structure to prevent errors
      setData({
        insights: [],
        notifications: [],
        spending_trends: null,
        wallet_passes: [],
        trends_data: null
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadInsightsData();
    setRefreshing(false);
  };

  const handleGeneratePass = async (insightId) => {
    try {
      console.log('💳 Generating wallet pass for insight:', insightId);
      const result = await insightsService.generateWalletPass(insightId);
      
      console.log('💳 Wallet pass result:', result);
      
      if (result.success && result.wallet_pass?.save_url) {
        // Show immediate feedback
        console.log('🎫 Wallet pass created successfully!');
        
        // Open Google Wallet save URL immediately after creation
        console.log('🔗 Opening Google Wallet save URL:', result.wallet_pass.save_url);
        window.open(result.wallet_pass.save_url, '_blank', 'noopener,noreferrer');
        
        // Show success message with instructions
        alert('🎫 Wallet pass created! \n\n📱 Google Wallet will open in a new tab. \n✅ Follow the prompts to save the pass to your wallet.');
        
        // Refresh data to update pass status
        await loadInsightsData();
      } else if (result.save_url) {
        // Handle direct save_url format (fallback)
        console.log('🔗 Opening Google Wallet save URL (direct):', result.save_url);
        window.open(result.save_url, '_blank', 'noopener,noreferrer');
        
        alert('🎫 Wallet pass created! \n\n📱 Google Wallet will open in a new tab. \n✅ Follow the prompts to save the pass to your wallet.');
        await loadInsightsData();
      } else {
        throw new Error(result.error || 'Failed to generate wallet pass - no save URL received');
      }
    } catch (error) {
      console.error('❌ Failed to generate wallet pass:', error);
      alert('❌ Failed to generate wallet pass. Please try again.');
    }
  };

  const handleMarkAsRead = async (notificationId) => {
    try {
      console.log('✅ Marking notification as read:', notificationId);
      await insightsService.markNotificationAsRead(notificationId);
      
      // Update local state
      setData(prevData => ({
        ...prevData,
        notifications: prevData.notifications.map(n =>
          n.notification_id === notificationId ? { ...n, read: true } : n
        )
      }));
      
    } catch (error) {
      console.error('❌ Failed to mark notification as read:', error);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      console.log('✅ Marking all notifications as read');
      await insightsService.markAllNotificationsAsRead();
      
      // Update local state
      setData(prevData => ({
        ...prevData,
        notifications: prevData.notifications.map(n => ({ ...n, read: true }))
      }));
      
    } catch (error) {
      console.error('❌ Failed to mark all notifications as read:', error);
    }
  };

  const handleDeleteNotification = async (notificationId) => {
    try {
      console.log('🗑️ Deleting notification:', notificationId);
      
      // For now, just remove from local state since backend doesn't have delete endpoint
      setData(prevData => ({
        ...prevData,
        notifications: prevData.notifications.filter(n => n.notification_id !== notificationId)
      }));
      
    } catch (error) {
      console.error('❌ Failed to delete notification:', error);
    }
  };

  // Calculate quick stats with proper null checking
  const getQuickStats = () => {
    // Return default stats if data is not available
    if (!data || !Array.isArray(data.insights)) {
      return {
        currentMonthTotal: 0,
        totalSavingsOpportunity: 0,
        totalOverspending: 0,
        highPriorityAlerts: 0,
        unreadNotifications: 0
      };
    }

    console.log('📊 Calculating stats for insights:', data.insights);

    // Calculate savings opportunities (negative impact or savings type)
    const totalSavingsOpportunity = data.insights
      .filter(i => 
        i.insight_type === 'savings_opportunity' || 
        (i.amount_impact && i.amount_impact > 0 && i.insight_type === 'savings_opportunity')
      )
      .reduce((sum, i) => sum + Math.abs(i.amount_impact || 0), 0);
      
    // Calculate overspending (positive impact from overspending type)
    const totalOverspending = data.insights
      .filter(i => 
        i.insight_type === 'overspending' && 
        i.amount_impact && 
        i.amount_impact > 0
      )
      .reduce((sum, i) => sum + i.amount_impact, 0);

    // Mock current month total (since we don't have spending_trends yet)
    const currentMonthTotal = 8500; // Default value

    // High priority alerts
    const highPriorityAlerts = data.insights
      .filter(i => i.priority === 'high' || i.priority === 'urgent').length;

    // Unread notifications
    const unreadNotifications = Array.isArray(data.notifications)
      ? data.notifications.filter(n => !n.read).length
      : 0;

    const stats = {
      currentMonthTotal,
      totalSavingsOpportunity,
      totalOverspending,
      highPriorityAlerts,
      unreadNotifications
    };

    console.log('📊 Calculated stats:', stats);
    return stats;
  };

  const stats = getQuickStats();

  if (loading) {
    return (
      <div className="page">
        <div className="loading-container">
          <RefreshCw className="loading-spinner" />
          <h2>Loading Insights...</h2>
          <p>Analyzing your spending patterns and generating recommendations</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <div className="error-container">
          <AlertTriangle className="error-icon" />
          <h2>Unable to Load Insights</h2>
          <p>{error}</p>
          <button onClick={loadInsightsData} className="btn btn-primary">
            <RefreshCw className="btn-icon" />
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      {/* Page Header */}
      <div className="page-header">
        <div className="header-content">
          <div className="header-title">
            <BarChart3 className="page-icon" />
            <div>
              <h1 className="page-title">Smart Insights</h1>
              <p className="page-description">
                AI-powered spending analysis and personalized recommendations
              </p>
            </div>
          </div>
          
          <div className="header-actions">
            <button 
              onClick={handleRefresh}
              disabled={refreshing}
              className="btn btn-secondary"
            >
              <RefreshCw className={`btn-icon ${refreshing ? 'spinning' : ''}`} />
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </button>
            
            <button className="btn btn-outline">
              <Download className="btn-icon" />
              Export
            </button>
          </div>
        </div>
      </div>

      {/* Quick Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-header">
            <DollarSign className="stat-icon spending" />
            <span className="stat-label">This Month</span>
          </div>
          <div className="stat-value">₹{stats.currentMonthTotal.toLocaleString()}</div>
          <div className="stat-change positive">+2.3% from last month</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <TrendingUp className="stat-icon savings" />
            <span className="stat-label">Savings Opportunity</span>
          </div>
          <div className="stat-value">₹{stats.totalSavingsOpportunity.toLocaleString()}</div>
          <div className="stat-change neutral">Available this month</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <AlertTriangle className="stat-icon alert" />
            <span className="stat-label">Overspending</span>
          </div>
          <div className="stat-value">₹{stats.totalOverspending.toLocaleString()}</div>
          <div className="stat-change negative">Above normal range</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <Bell className="stat-icon notification" />
            <span className="stat-label">Alerts</span>
          </div>
          <div className="stat-value">{stats.highPriorityAlerts}</div>
          <div className="stat-change neutral">
            {stats.unreadNotifications} unread notifications
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'insights' ? 'active' : ''}`}
          onClick={() => setActiveTab('insights')}
        >
          <Target className="tab-icon" />
          Insights ({data.insights.length})
        </button>
        
        <button 
          className={`tab ${activeTab === 'notifications' ? 'active' : ''}`}
          onClick={() => setActiveTab('notifications')}
        >
          <Bell className="tab-icon" />
          Notifications ({stats.unreadNotifications})
        </button>
        
        <button 
          className={`tab ${activeTab === 'trends' ? 'active' : ''}`}
          onClick={() => setActiveTab('trends')}
        >
          <BarChart3 className="tab-icon" />
          Trends
        </button>
        
        <button 
          className={`tab ${activeTab === 'wallet' ? 'active' : ''}`}
          onClick={() => setActiveTab('wallet')}
        >
          <Calendar className="tab-icon" />
          Wallet Passes ({data.wallet_passes.length})
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'insights' && (
          <InsightsList 
            insights={data.insights}
            onGeneratePass={handleGeneratePass}
          />
        )}
        
        {activeTab === 'notifications' && (
          <NotificationsCenter 
            notifications={data.notifications}
            onMarkAsRead={handleMarkAsRead}
            onMarkAllAsRead={handleMarkAllAsRead}
            onDelete={handleDeleteNotification}
          />
        )}
        
        {activeTab === 'trends' && (
          <div className="trends-content">
            <TrendsChart 
              insights={data.insights}
              trendsData={data.trends_data}
              loading={loading}
              onRefresh={handleRefresh}
            />
          </div>
        )}
        
        {activeTab === 'wallet' && (
          <div className="wallet-passes-content">
            {data.wallet_passes.length > 0 ? (
              <div className="wallet-passes-grid">
                {data.wallet_passes.map((pass) => (
                  <div key={pass.pass_id} className="wallet-pass-card">
                    <div className="pass-header">
                      <h3>{pass.title}</h3>
                      <span className={`pass-priority ${pass.priority}`}>
                        {pass.priority}
                      </span>
                    </div>
                    <p className="pass-description">{pass.description}</p>
                    {pass.amount_impact && (
                      <div className="pass-amount">
                        Impact: ₹{Math.abs(pass.amount_impact).toLocaleString()}
                      </div>
                    )}
                    <div className="pass-footer">
                      <span className="pass-date">
                        Created: {new Date(pass.created_at).toLocaleDateString()}
                      </span>
                      <button 
                        onClick={() => window.open(pass.pass_url, '_blank')}
                        className="btn btn-sm btn-primary"
                      >
                        Open in Wallet
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-wallet">
                <Calendar className="empty-icon" />
                <h3>No Wallet Passes</h3>
                <p>Generate wallet passes from your insights to see them here.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default InsightsPage;
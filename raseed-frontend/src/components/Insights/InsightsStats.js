import React from 'react';
import { StatsCard, StatsGrid } from './StatsGrid';
import { FaCalendarAlt, FaPiggyBank, FaExclamationTriangle, FaBell } from 'react-icons/fa';

/**
 * InsightsStats component that displays the financial metrics grid
 * as seen in the dashboard
 */
const InsightsStats = () => {
  return (
    <StatsGrid>
      <StatsCard 
        title="This Month" 
        value="8,500" 
        currencySymbol="₹"
        change={2.3}
        changeType="positive"
        message="from last month"
        icon={<FaCalendarAlt />}
        iconBgColor="#EBF5FF"
        iconColor="#3B82F6"
      />
      
      <StatsCard 
        title="Savings Opportunity" 
        value="9,800" 
        currencySymbol="₹"
        message="Available this month"
        icon={<FaPiggyBank />}
        iconBgColor="#DCFCE7"
        iconColor="#16A34A"
      />
      
      <StatsCard 
        title="Overspending" 
        value="1,200" 
        currencySymbol="₹"
        message="Above normal range"
        icon={<FaExclamationTriangle />}
        iconBgColor="#FEF3C7"
        iconColor="#D97706"
      />
      
      <StatsCard 
        title="Alerts" 
        value="1" 
        notifications={3}
        message="unread notifications"
        icon={<FaBell />}
        iconBgColor="#FEE2E2"
        iconColor="#DC2626"
      />
    </StatsGrid>
  );
};

export default InsightsStats;

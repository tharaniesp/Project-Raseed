// src/components/Insights/InsightCard.js
import React, { useState } from 'react';
import { 
  TrendingUp, TrendingDown, AlertTriangle, Wallet, 
  CheckCircle, Calendar, Target, RefreshCw 
} from 'lucide-react';
import './InsightCard.css';

const priorityConfig = {
  urgent: {
    className: 'insight-urgent',
    icon: AlertTriangle,
    color: '#ef4444'
  },
  high: {
    className: 'insight-high', 
    icon: TrendingUp,
    color: '#f97316'
  },
  medium: {
    className: 'insight-medium',
    icon: Target,
    color: '#eab308'
  },
  low: {
    className: 'insight-low',
    icon: TrendingDown,
    color: '#3b82f6'
  }
};

const InsightCard = ({ insight, onGeneratePass }) => {
  const [isGeneratingPass, setIsGeneratingPass] = useState(false);
  
  const config = priorityConfig[insight.priority] || priorityConfig.low;
  const IconComponent = config.icon;
  const isPositiveImpact = insight.amount_impact < 0;

  const handleGeneratePass = async () => {
    if (!insight.wallet_pass_eligible) return;
    
    setIsGeneratingPass(true);
    try {
      await onGeneratePass(insight.insight_id);
    } catch (error) {
      console.error('Failed to generate pass:', error);
    } finally {
      setIsGeneratingPass(false);
    }
  };

  const formatAmount = (amount) => {
    return `₹${Math.abs(amount).toLocaleString()}`;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  };

  return (
    <div className={`insight-card ${config.className}`}>
      <div className="insight-header">
        <div className="insight-title-section">
          <div className="insight-icon-wrapper">
            <IconComponent 
              className="insight-icon" 
              style={{ color: config.color }}
            />
          </div>
          <div className="insight-title-content">
            <h3 className="insight-title">{insight.title}</h3>
            <p className="insight-description">{insight.description}</p>
          </div>
        </div>
        
        <div className="insight-actions">
          <div className={`insight-amount ${isPositiveImpact ? 'positive' : 'negative'}`}>
            {isPositiveImpact ? '-' : '+'}
            {formatAmount(insight.amount_impact)}
          </div>
          
          {insight.wallet_pass_eligible && (
            <button
              onClick={handleGeneratePass}
              disabled={isGeneratingPass}
              className="btn btn-wallet"
            >
              {isGeneratingPass ? (
                <>
                  <RefreshCw className="btn-icon spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Wallet className="btn-icon" />
                  Add to Wallet
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {insight.actionable_suggestions && insight.actionable_suggestions.length > 0 && (
        <div className="insight-suggestions">
          <h4 className="suggestions-title">💡 Suggested Actions:</h4>
          <ul className="suggestions-list">
            {insight.actionable_suggestions.map((suggestion, index) => (
              <li key={index} className="suggestion-item">
                <CheckCircle className="suggestion-icon" />
                <span>{suggestion}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="insight-metadata">
        <div className="metadata-item">
          <Calendar className="metadata-icon" />
          <span>{insight.time_period}</span>
        </div>
        {insight.category && (
          <div className="metadata-item">
            <Target className="metadata-icon" />
            <span>{insight.category}</span>
          </div>
        )}
        <div className="metadata-item">
          <span className="metadata-date">
            {formatDate(insight.created_at)}
          </span>
        </div>
      </div>
    </div>
  );
};

export default InsightCard;
// src/components/Insights/TrendsChart.js
import React, { useState, useEffect, useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  Filler
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import { format, parseISO, subDays, startOfDay } from 'date-fns';
import { 
  TrendingUp, TrendingDown, BarChart3, LineChart, 
  Calendar, Filter, Download, RefreshCw 
} from 'lucide-react';
import './TrendsChart.css';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  Filler
);

const TrendsChart = ({ insights, loading = false, onRefresh }) => {
  const [chartType, setChartType] = useState('line');
  const [timeRange, setTimeRange] = useState('7d');
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [isExpanded, setIsExpanded] = useState(false);

  // Color palette for different categories
  const colorPalette = {
    groceries: '#10b981',
    dining: '#f59e0b',
    transportation: '#3b82f6',
    entertainment: '#8b5cf6',
    healthcare: '#ef4444',
    shopping: '#f97316',
    utilities: '#06b6d4',
    other: '#6b7280'
  };

  // Extract trends data from insights
  const trendsData = useMemo(() => {
    if (!insights || insights.length === 0) {
      return generateMockTrendsData();
    }

    // Process real insights data
    const categorySpending = {};
    const dailySpending = {};

    insights.forEach(insight => {
      if (insight.category && insight.amount_impact) {
        const category = insight.category.toLowerCase();
        const date = insight.created_at ? format(parseISO(insight.created_at), 'yyyy-MM-dd') : format(new Date(), 'yyyy-MM-dd');
        
        // Category totals
        if (!categorySpending[category]) {
          categorySpending[category] = 0;
        }
        categorySpending[category] += Math.abs(insight.amount_impact);

        // Daily spending
        if (!dailySpending[date]) {
          dailySpending[date] = {};
        }
        if (!dailySpending[date][category]) {
          dailySpending[date][category] = 0;
        }
        dailySpending[date][category] += Math.abs(insight.amount_impact);
      }
    });

    // Generate time series data for the selected time range
    const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 90;
    const dates = Array.from({ length: days }, (_, i) => 
      format(subDays(new Date(), days - 1 - i), 'yyyy-MM-dd')
    );

    const categories = Object.keys(categorySpending);
    
    return {
      dates,
      categories,
      categorySpending,
      dailySpending
    };
  }, [insights, timeRange]);

  // Generate mock data for demonstration
  function generateMockTrendsData() {
    const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 90;
    const dates = Array.from({ length: days }, (_, i) => 
      format(subDays(new Date(), days - 1 - i), 'yyyy-MM-dd')
    );

    const categories = ['groceries', 'dining', 'transportation', 'entertainment', 'shopping'];
    const categorySpending = {};
    const dailySpending = {};

    categories.forEach(category => {
      categorySpending[category] = 0;
      dates.forEach(date => {
        if (!dailySpending[date]) {
          dailySpending[date] = {};
        }
        // Generate realistic spending patterns
        const baseAmount = {
          groceries: 150,
          dining: 80,
          transportation: 50,
          entertainment: 40,
          shopping: 60
        }[category] || 30;
        
        const variance = Math.random() * 0.5 + 0.5; // 0.5 to 1.0 multiplier
        const amount = Math.round(baseAmount * variance);
        
        dailySpending[date][category] = amount;
        categorySpending[category] += amount;
      });
    });

    return {
      dates,
      categories,
      categorySpending,
      dailySpending
    };
  }

  // Prepare chart data
  const chartData = useMemo(() => {
    const { dates, categories, dailySpending } = trendsData;
    const activeCategories = selectedCategories.length > 0 ? selectedCategories : categories;

    const datasets = activeCategories.map(category => ({
      label: category.charAt(0).toUpperCase() + category.slice(1),
      data: dates.map(date => dailySpending[date]?.[category] || 0),
      borderColor: colorPalette[category] || colorPalette.other,
      backgroundColor: chartType === 'line' 
        ? `${colorPalette[category] || colorPalette.other}20`
        : colorPalette[category] || colorPalette.other,
      borderWidth: 2,
      fill: chartType === 'line',
      tension: 0.3,
    }));

    return {
      labels: dates.map(date => format(parseISO(date), 'MMM dd')),
      datasets
    };
  }, [trendsData, selectedCategories, chartType]);

  // Chart options
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          usePointStyle: true,
          padding: 20,
          font: {
            size: 12
          }
        }
      },
      title: {
        display: true,
        text: `Spending Trends - Last ${timeRange === '7d' ? '7 Days' : timeRange === '30d' ? '30 Days' : '90 Days'}`,
        font: {
          size: 16,
          weight: 'bold'
        },
        padding: {
          top: 10,
          bottom: 30
        }
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        titleColor: '#374151',
        bodyColor: '#374151',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        cornerRadius: 8,
        padding: 12,
        callbacks: {
          label: function(context) {
            return `${context.dataset.label}: ₹${context.parsed.y.toLocaleString()}`;
          }
        }
      }
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Date',
          font: {
            weight: 'bold'
          }
        },
        grid: {
          color: '#f3f4f6'
        }
      },
      y: {
        display: true,
        title: {
          display: true,
          text: 'Amount (₹)',
          font: {
            weight: 'bold'
          }
        },
        grid: {
          color: '#f3f4f6'
        },
        ticks: {
          callback: function(value) {
            return '₹' + value.toLocaleString();
          }
        }
      }
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false
    },
    elements: {
      point: {
        radius: 4,
        hoverRadius: 6
      }
    }
  };

  // Toggle category selection
  const toggleCategory = (category) => {
    setSelectedCategories(prev => {
      if (prev.includes(category)) {
        return prev.filter(c => c !== category);
      } else {
        return [...prev, category];
      }
    });
  };

  // Export chart data
  const exportData = () => {
    const { dates, categories, categorySpending, dailySpending } = trendsData;
    
    // Prepare CSV data
    const csvData = [];
    
    // Add header row
    const headers = ['Date', ...categories];
    csvData.push(headers.join(','));
    
    // Add data rows
    dates.forEach(date => {
      const row = [date];
      categories.forEach(category => {
        row.push(dailySpending[date]?.[category] || 0);
      });
      csvData.push(row.join(','));
    });
    
    // Add summary row
    csvData.push(''); // Empty line
    csvData.push('Category Totals');
    categories.forEach(category => {
      csvData.push(`${category},${categorySpending[category] || 0}`);
    });
    
    // Create and download file
    const csvContent = csvData.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `spending_trends_${timeRange}_${format(new Date(), 'yyyy-MM-dd')}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  // Calculate total spending and trend
  const { totalSpending, trendDirection, trendPercentage } = useMemo(() => {
    const { categorySpending } = trendsData;
    const total = Object.values(categorySpending).reduce((sum, amount) => sum + amount, 0);
    
    // Simple trend calculation (comparing first half vs second half of period)
    const { dates, dailySpending } = trendsData;
    const midPoint = Math.floor(dates.length / 2);
    const firstHalf = dates.slice(0, midPoint);
    const secondHalf = dates.slice(midPoint);
    
    const firstHalfTotal = firstHalf.reduce((sum, date) => {
      const dayTotal = Object.values(dailySpending[date] || {}).reduce((s, a) => s + a, 0);
      return sum + dayTotal;
    }, 0);
    
    const secondHalfTotal = secondHalf.reduce((sum, date) => {
      const dayTotal = Object.values(dailySpending[date] || {}).reduce((s, a) => s + a, 0);
      return sum + dayTotal;
    }, 0);
    
    const avgFirst = firstHalfTotal / firstHalf.length;
    const avgSecond = secondHalfTotal / secondHalf.length;
    const percentChange = avgFirst > 0 ? ((avgSecond - avgFirst) / avgFirst) * 100 : 0;
    
    return {
      totalSpending: total,
      trendDirection: percentChange > 0 ? 'up' : 'down',
      trendPercentage: Math.abs(percentChange)
    };
  }, [trendsData]);

  if (loading) {
    return (
      <div className="trends-chart-container loading">
        <div className="loading-content">
          <RefreshCw className="loading-spinner" />
          <p>Loading trends data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`trends-chart-container ${isExpanded ? 'expanded' : ''}`}>
      <div className="trends-header">
        <div className="trends-header-top">
          <div className="trends-title">
            <BarChart3 className="trends-icon" />
            <h3>Spending Trends</h3>
          </div>
          
          <div className="trends-summary">
            <div className="total-spending">
              <span className="label">Total Spending:</span>
              <span className="amount">₹{totalSpending.toLocaleString()}</span>
            </div>
            <div className={`trend-indicator ${trendDirection}`}>
              {trendDirection === 'up' ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
              <span>{trendPercentage.toFixed(1)}%</span>
            </div>
          </div>
        </div>

        <div className="trends-controls">
          <div className="control-group">
            <label>Chart Type:</label>
            <div className="button-group">
              <button
                className={`control-btn ${chartType === 'line' ? 'active' : ''}`}
                onClick={() => setChartType('line')}
              >
                <LineChart size={16} />
                Line
              </button>
              <button
                className={`control-btn ${chartType === 'bar' ? 'active' : ''}`}
                onClick={() => setChartType('bar')}
              >
                <BarChart3 size={16} />
                Bar
              </button>
            </div>
          </div>

          <div className="control-group">
            <label>Time Range:</label>
            <select 
              value={timeRange} 
              onChange={(e) => setTimeRange(e.target.value)}
              className="time-select"
            >
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
            </select>
          </div>

          <button 
            className="control-btn refresh-btn"
            onClick={onRefresh}
            disabled={loading}
          >
            <RefreshCw size={16} />
            Refresh
          </button>
        </div>
      </div>

      <div className="categories-filter">
        <h4>Categories:</h4>
        <div className="category-chips">
          {trendsData.categories.map(category => (
            <button
              key={category}
              className={`category-chip ${selectedCategories.includes(category) || selectedCategories.length === 0 ? 'active' : ''}`}
              style={{ 
                backgroundColor: selectedCategories.includes(category) || selectedCategories.length === 0 
                  ? colorPalette[category] || colorPalette.other 
                  : '#f3f4f6',
                color: selectedCategories.includes(category) || selectedCategories.length === 0 ? 'white' : '#6b7280'
              }}
              onClick={() => toggleCategory(category)}
            >
              {category.charAt(0).toUpperCase() + category.slice(1)}
              <span className="category-amount">
                ₹{trendsData.categorySpending[category]?.toLocaleString() || 0}
              </span>
            </button>
          ))}
        </div>
      </div>

      <div className="chart-container">
        {chartType === 'line' ? (
          <Line data={chartData} options={chartOptions} />
        ) : (
          <Bar data={chartData} options={chartOptions} />
        )}
      </div>

      <div className="chart-footer">
        {/* <button 
          className="expand-btn"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? 'Collapse View' : 'Expand View'}
        </button> */}
        
        <div className="chart-actions">
          <button 
            className="action-btn"
            onClick={exportData}
            title="Export data as CSV"
          >
            <Download size={16} />
            Export
          </button>
        </div>
      </div>
    </div>
  );
};

export default TrendsChart;

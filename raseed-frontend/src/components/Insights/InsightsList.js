// src/components/Insights/InsightsList.js
import React, { useState, useMemo } from 'react';
import { Filter, SortAsc, SortDesc, Search, AlertCircle } from 'lucide-react';
import InsightCard from './InsightCard';
import './InsightsList.css';

const InsightsList = ({ insights, onGeneratePass, loading = false }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedPriority, setSelectedPriority] = useState('all');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');

  // Get unique categories from insights
  const categories = useMemo(() => {
    const uniqueCategories = [...new Set(insights
      .map(insight => insight.category)
      .filter(Boolean))];
    return uniqueCategories.sort();
  }, [insights]);

  // Filter and sort insights
  const filteredAndSortedInsights = useMemo(() => {
    let filtered = insights;

    // Apply search filter
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter(insight =>
        insight.title.toLowerCase().includes(searchLower) ||
        insight.description.toLowerCase().includes(searchLower) ||
        insight.category?.toLowerCase().includes(searchLower)
      );
    }

    // Apply priority filter
    if (selectedPriority !== 'all') {
      filtered = filtered.filter(insight => insight.priority === selectedPriority);
    }

    // Apply category filter
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(insight => insight.category === selectedCategory);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue, bValue;

      switch (sortBy) {
        case 'created_at':
          aValue = new Date(a.created_at);
          bValue = new Date(b.created_at);
          break;
        case 'amount_impact':
          aValue = Math.abs(a.amount_impact || 0);
          bValue = Math.abs(b.amount_impact || 0);
          break;
        case 'priority':
          const priorityOrder = { urgent: 4, high: 3, medium: 2, low: 1 };
          aValue = priorityOrder[a.priority] || 0;
          bValue = priorityOrder[b.priority] || 0;
          break;
        case 'title':
          aValue = a.title.toLowerCase();
          bValue = b.title.toLowerCase();
          break;
        default:
          return 0;
      }

      if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return filtered;
  }, [insights, searchTerm, selectedPriority, selectedCategory, sortBy, sortOrder]);

  const handleSortChange = (newSortBy) => {
    if (sortBy === newSortBy) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(newSortBy);
      setSortOrder('desc');
    }
  };

  const getSortIcon = (field) => {
    if (sortBy !== field) return null;
    return sortOrder === 'asc' ? <SortAsc className="sort-icon" /> : <SortDesc className="sort-icon" />;
  };

  const clearFilters = () => {
    setSearchTerm('');
    setSelectedPriority('all');
    setSelectedCategory('all');
    setSortBy('created_at');
    setSortOrder('desc');
  };

  const activeFiltersCount = [
    searchTerm,
    selectedPriority !== 'all' ? selectedPriority : null,
    selectedCategory !== 'all' ? selectedCategory : null
  ].filter(Boolean).length;

  if (loading) {
    return (
      <div className="insights-loading">
        <div className="loading-spinner"></div>
        <p>Loading insights...</p>
      </div>
    );
  }

  return (
    <div className="insights-list">
      {/* Controls Section */}
      <div className="insights-controls">
        <div className="search-section">
          <div className="search-box">
            <Search className="search-icon" />
            <input
              type="text"
              placeholder="Search insights..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>
        </div>

        <div className="filter-section">
          <div className="filter-group">
            <label htmlFor="priority-filter" className="filter-label">
              <Filter className="filter-icon" />
              Priority:
            </label>
            <select
              id="priority-filter"
              value={selectedPriority}
              onChange={(e) => setSelectedPriority(e.target.value)}
              className="filter-select"
            >
              <option value="all">All Priorities</option>
              <option value="urgent">Urgent</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="category-filter" className="filter-label">
              Category:
            </label>
            <select
              id="category-filter"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="filter-select"
            >
              <option value="all">All Categories</option>
              {categories.map(category => (
                <option key={category} value={category}>
                  {category.charAt(0).toUpperCase() + category.slice(1)}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="sort-section">
          <span className="sort-label">Sort by:</span>
          <div className="sort-buttons">
            <button
              onClick={() => handleSortChange('created_at')}
              className={`sort-btn ${sortBy === 'created_at' ? 'active' : ''}`}
            >
              Date {getSortIcon('created_at')}
            </button>
            <button
              onClick={() => handleSortChange('priority')}
              className={`sort-btn ${sortBy === 'priority' ? 'active' : ''}`}
            >
              Priority {getSortIcon('priority')}
            </button>
            <button
              onClick={() => handleSortChange('amount_impact')}
              className={`sort-btn ${sortBy === 'amount_impact' ? 'active' : ''}`}
            >
              Impact {getSortIcon('amount_impact')}
            </button>
          </div>
        </div>

        {activeFiltersCount > 0 && (
          <div className="active-filters">
            <span className="active-filters-text">
              {activeFiltersCount} filter{activeFiltersCount > 1 ? 's' : ''} active
            </span>
            <button onClick={clearFilters} className="clear-filters-btn">
              Clear all
            </button>
          </div>
        )}
      </div>

      {/* Results Summary */}
      <div className="results-summary">
        <p className="results-count">
          Showing {filteredAndSortedInsights.length} of {insights.length} insights
        </p>
      </div>

      {/* Insights Grid */}
      {filteredAndSortedInsights.length > 0 ? (
        <div className="insights-grid">
          {filteredAndSortedInsights.map((insight) => (
            <InsightCard
              key={insight.insight_id}
              insight={insight}
              onGeneratePass={onGeneratePass}
            />
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <AlertCircle className="empty-icon" />
          <h3>No insights found</h3>
          <p>
            {insights.length === 0
              ? "No insights have been generated yet. Upload some receipts to get started!"
              : "No insights match your current filters. Try adjusting your search criteria."
            }
          </p>
          {activeFiltersCount > 0 && (
            <button onClick={clearFilters} className="btn btn-secondary">
              Clear filters
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default InsightsList;
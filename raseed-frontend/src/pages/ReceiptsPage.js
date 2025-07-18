// src/pages/ReceiptsPage.js
import React, { useEffect, useState } from 'react';
import { Search, Filter, Calendar, DollarSign } from 'lucide-react';
import { useReceipt } from '../context/ReceiptContext';
import ReceiptCard from '../components/Receipt/ReceiptCard';

const ReceiptsPage = () => {
  const { receipts, loading, error, actions } = useReceipt();
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('date');

  useEffect(() => {
    console.log('🔍 ReceiptsPage: Loading receipts...');
    actions.loadReceipts();
  }, []);

  // Add debug logging
  useEffect(() => {
    console.log('📊 ReceiptsPage Debug:', {
      receiptsCount: receipts.length,
      loading,
      error,
      receipts: receipts
    });
  }, [receipts, loading, error]);

  const filteredReceipts = receipts.filter(receipt => {
    const filename = receipt.file_metadata?.original_filename || receipt.file_metadata?.filename || '';
    const merchantName = receipt.extracted_data?.merchant_name || '';
    
    return filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
           merchantName.toLowerCase().includes(searchTerm.toLowerCase());
  });

  const sortedReceipts = [...filteredReceipts].sort((a, b) => {
    switch (sortBy) {
      case 'date':
        return new Date(b.created_at) - new Date(a.created_at);
      case 'amount':
        const amountA = a.extracted_data?.total_amount || 0;
        const amountB = b.extracted_data?.total_amount || 0;
        return amountB - amountA;
      case 'merchant':
        const merchantA = a.extracted_data?.merchant_name || '';
        const merchantB = b.extracted_data?.merchant_name || '';
        return merchantA.localeCompare(merchantB);
      default:
        return 0;
    }
  });

  console.log('🎯 Filtered and sorted receipts:', sortedReceipts);

  if (loading) {
    return (
      <div className="page">
        <div className="loading">
          <div className="spinner"></div>
          <span>Loading receipts...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">My Receipts</h1>
        <p className="page-description">
          View and manage all your uploaded receipts
        </p>
      </div>

      {/* Debug Info */}
      <div style={{ background: '#f0f0f0', padding: '10px', marginBottom: '20px', fontSize: '12px' }}>
        <strong>Debug Info:</strong> 
        Loading: {loading.toString()}, 
        Error: {error || 'none'}, 
        Receipts Count: {receipts.length}, 
        Filtered Count: {filteredReceipts.length}
      </div>

      {/* Search and Filter */}
      <div className="receipts-controls">
        <div className="search-box">
          <Search size={20} />
          <input
            type="text"
            placeholder="Search receipts..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>
        
        <div className="sort-controls">
          <Filter size={20} />
          <select 
            value={sortBy} 
            onChange={(e) => setSortBy(e.target.value)}
            className="sort-select"
          >
            <option value="date">Sort by Date</option>
            <option value="amount">Sort by Amount</option>
            <option value="merchant">Sort by Merchant</option>
          </select>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="error-message">
          <p>Error loading receipts: {error}</p>
          <button onClick={() => actions.loadReceipts()} className="btn btn-primary">
            Retry
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && sortedReceipts.length === 0 && !error && (
        <div className="empty-state">
          <Calendar size={48} />
          <h3>No receipts found</h3>
          <p>Upload your first receipt to get started!</p>
          <a href="/upload" className="btn btn-primary">
            Upload Receipt
          </a>
        </div>
      )}

      {/* Receipts Grid */}
      {sortedReceipts.length > 0 && (
        <div className="receipts-grid">
          {sortedReceipts.map((receipt) => {
            console.log('🎫 Rendering receipt:', receipt);
            return (
              <ReceiptCard key={receipt.id} receipt={receipt} />
            );
          })}
        </div>
      )}

      {/* Summary Stats */}
      {sortedReceipts.length > 0 && (
        <div className="receipts-summary">
          <div className="stat-card">
            <DollarSign size={24} />
            <div>
              <h4>Total Spent</h4>
              <p>
                ${sortedReceipts
                  .reduce((sum, r) => sum + (r.extracted_data?.total_amount || 0), 0)
                  .toFixed(2)}
              </p>
            </div>
          </div>
          <div className="stat-card">
            <Calendar size={24} />
            <div>
              <h4>This Month</h4>
              <p>{sortedReceipts.length} receipts</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReceiptsPage;
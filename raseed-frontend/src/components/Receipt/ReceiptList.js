/ src/components/Receipt/ReceiptList.js
import React, { useState } from 'react';
import { Grid, List, ChevronLeft, ChevronRight } from 'lucide-react';
import ReceiptCard from './ReceiptCard';

const ReceiptList = ({ receipts, loading, onLoadMore, hasMore = false }) => {
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 12;

  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedReceipts = receipts.slice(startIndex, endIndex);
  const totalPages = Math.ceil(receipts.length / itemsPerPage);

  const handlePrevPage = () => {
    setCurrentPage(prev => Math.max(1, prev - 1));
  };

  const handleNextPage = () => {
    setCurrentPage(prev => Math.min(totalPages, prev + 1));
  };

  if (loading) {
    return (
      <div className="receipt-list-loading">
        <div className="loading-grid">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="receipt-card-skeleton">
              <div className="skeleton-header"></div>
              <div className="skeleton-content">
                <div className="skeleton-line"></div>
                <div className="skeleton-line short"></div>
                <div className="skeleton-line"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="receipt-list">
      {/* View Controls */}
      <div className="list-controls">
        <div className="view-toggle">
          <button
            className={`toggle-btn ${viewMode === 'grid' ? 'active' : ''}`}
            onClick={() => setViewMode('grid')}
          >
            <Grid size={16} />
            Grid
          </button>
          <button
            className={`toggle-btn ${viewMode === 'list' ? 'active' : ''}`}
            onClick={() => setViewMode('list')}
          >
            <List size={16} />
            List
          </button>
        </div>

        <div className="list-stats">
          Showing {startIndex + 1}-{Math.min(endIndex, receipts.length)} of {receipts.length}
        </div>
      </div>

      {/* Receipts Grid/List */}
      <div className={`receipts-container ${viewMode}`}>
        {paginatedReceipts.map((receipt) => (
          <ReceiptCard key={receipt.id} receipt={receipt} />
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination">
          <button
            className="pagination-btn"
            onClick={handlePrevPage}
            disabled={currentPage === 1}
          >
            <ChevronLeft size={16} />
            Previous
          </button>

          <div className="pagination-info">
            <span>Page {currentPage} of {totalPages}</span>
          </div>

          <button
            className="pagination-btn"
            onClick={handleNextPage}
            disabled={currentPage === totalPages}
          >
            Next
            <ChevronRight size={16} />
          </button>
        </div>
      )}

      {/* Load More (for infinite scroll alternative) */}
      {hasMore && (
        <div className="load-more">
          <button onClick={onLoadMore} className="btn btn-secondary">
            Load More Receipts
          </button>
        </div>
      )}
    </div>
  );
};

export default ReceiptList;
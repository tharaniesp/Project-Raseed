// src/components/Receipt/ReceiptCard.js
import React from 'react';
import { Calendar, DollarSign, MapPin, FileText, Eye, Download } from 'lucide-react';

const ReceiptCard = ({ receipt }) => {
  console.log('🎫 ReceiptCard received:', receipt);

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount || 0);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'processed': return 'green';
      case 'processing': return 'blue';
      case 'error': return 'red';
      default: return 'gray';
    }
  };

  const handleView = () => {
    if (receipt.download_url) {
      window.open(receipt.download_url, '_blank');
    }
  };

  const handleDownload = () => {
    if (receipt.download_url) {
      const link = document.createElement('a');
      link.href = receipt.download_url;
      link.download = receipt.file_metadata?.original_filename || 
                     receipt.file_metadata?.filename || 
                     'receipt';
      link.click();
    }
  };

  // 🔧 FIX: Handle both API response format and local state format
  const getFileName = () => {
    return receipt.file_metadata?.original_filename || 
           receipt.file_metadata?.filename || 
           'Receipt';
  };

  const getFileType = () => {
    return receipt.file_metadata?.content_type?.split('/')[1]?.toUpperCase() || 'FILE';
  };

  return (
    <div className="receipt-card">
      {/* Card Header */}
      <div className="receipt-card-header">
        <div className="receipt-info">
          <h3 className="receipt-title">
            {receipt.extracted_data?.merchant_name || getFileName()}
          </h3>
          <span className={`status-badge status-${getStatusColor(receipt.status)}`}>
            {receipt.status}
          </span>
        </div>
        
        <div className="receipt-actions">
          <button 
            onClick={handleView}
            className="action-btn"
            title="View Receipt"
          >
            <Eye size={16} />
          </button>
          <button 
            onClick={handleDownload}
            className="action-btn"
            title="Download"
          >
            <Download size={16} />
          </button>
        </div>
      </div>

      {/* Card Content */}
      <div className="receipt-card-content">
        {/* Amount */}
        {receipt.extracted_data?.total_amount && (
          <div className="receipt-amount">
            <DollarSign size={20} />
            <span className="amount">
              {formatCurrency(receipt.extracted_data.total_amount)}
            </span>
          </div>
        )}

        {/* Details */}
        <div className="receipt-details">
          <div className="detail-item">
            <Calendar size={16} />
            <span>
              {receipt.extracted_data?.receipt_date || formatDate(receipt.created_at)}
            </span>
          </div>
          
          {receipt.extracted_data?.merchant_address && (
            <div className="detail-item">
              <MapPin size={16} />
              <span>{receipt.extracted_data.merchant_address}</span>
            </div>
          )}
          
          <div className="detail-item">
            <FileText size={16} />
            <span>{getFileType()}</span>
          </div>

          {/* 🔧 ADD: File size info */}
          <div className="detail-item">
            <FileText size={16} />
            <span>
              {receipt.file_metadata?.file_size ? 
                `${(receipt.file_metadata.file_size / 1024).toFixed(1)} KB` : 
                'Unknown size'
              }
            </span>
          </div>
        </div>

        {/* Items Preview */}
        {receipt.extracted_data?.items && receipt.extracted_data.items.length > 0 && (
          <div className="items-preview">
            <h4>Items ({receipt.extracted_data.items.length})</h4>
            <div className="items-list">
              {receipt.extracted_data.items.slice(0, 3).map((item, index) => (
                <div key={index} className="item">
                  <span className="item-name">{item.name}</span>
                  {item.total_price && (
                    <span className="item-price">{formatCurrency(item.total_price)}</span>
                  )}
                </div>
              ))}
              {receipt.extracted_data.items.length > 3 && (
                <div className="more-items">
                  +{receipt.extracted_data.items.length - 3} more items
                </div>
              )}
            </div>
          </div>
        )}

        {/* Processing Status */}
        {receipt.status === 'uploaded' && (
          <div className="processing-notice">
            <span>✨ Ready for AI processing (Step 2)</span>
          </div>
        )}
        
        {receipt.status === 'processing' && (
          <div className="processing-notice">
            <div className="spinner small"></div>
            <span>Extracting data...</span>
          </div>
        )}

        {/* 🔧 ADD: Debug info in development */}
        {process.env.NODE_ENV === 'development' && (
          <div style={{ 
            fontSize: '10px', 
            background: '#f0f0f0', 
            padding: '5px', 
            marginTop: '10px',
            borderRadius: '4px'
          }}>
            <strong>Debug:</strong> ID: {receipt.id}, 
            Status: {receipt.status}, 
            File: {getFileName()}
          </div>
        )}
      </div>
    </div>
  );
};

export default ReceiptCard;
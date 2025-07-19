// src/components/Receipt/ReceiptCard.js
import React, { useState } from 'react';
import { Calendar, DollarSign, MapPin, FileText, Eye, Download, Brain, Loader, CheckCircle, AlertTriangle } from 'lucide-react';
import { receiptService } from '../../services/receiptService';

const ReceiptCard = ({ receipt }) => {
  const [processing, setProcessing] = useState(false);
  const [localReceipt, setLocalReceipt] = useState(receipt);

  console.log('🎫 ReceiptCard received:', localReceipt);

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
    if (localReceipt.download_url) {
      window.open(localReceipt.download_url, '_blank');
    }
  };

  const handleDownload = () => {
    if (localReceipt.download_url) {
      const link = document.createElement('a');
      link.href = localReceipt.download_url;
      link.download = localReceipt.file_metadata?.original_filename || 
                     localReceipt.file_metadata?.filename || 
                     'receipt';
      link.click();
    }
  };

  const handleProcessWithAI = async () => {
    setProcessing(true);
    try {
      console.log('🤖 Processing receipt with AI:', localReceipt.id);
      const result = await receiptService.processReceipt(localReceipt.id);
      
      if (result.success) {
        // Update local state with processed data
        setLocalReceipt(prev => ({
          ...prev,
          status: 'processed',
          extracted_data: result.extracted_data
        }));
        
        console.log('✅ AI processing successful:', result);
      }
    } catch (error) {
      console.error('❌ AI processing failed:', error);
      setLocalReceipt(prev => ({
        ...prev,
        status: 'error',
        processing_error: error.message
      }));
    } finally {
      setProcessing(false);
    }
  };

  // 🔧 FIX: Handle both API response format and local state format
  const getFileName = () => {
    return localReceipt.file_metadata?.original_filename || 
           localReceipt.file_metadata?.filename || 
           'Receipt';
  };

  const getFileType = () => {
    return localReceipt.file_metadata?.content_type?.split('/')[1]?.toUpperCase() || 'FILE';
  };

  return (
    <div className="receipt-card">
      {/* Card Header */}
      <div className="receipt-card-header">
        <div className="receipt-info">
          <h3 className="receipt-title">
            {localReceipt.extracted_data?.merchant_name || getFileName()}
          </h3>
          <span className={`status-badge status-${getStatusColor(localReceipt.status)}`}>
            {localReceipt.status}
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
          
          {/* AI Processing Button - Step 2 */}
          {localReceipt.status === 'uploaded' && (
            <button 
              onClick={handleProcessWithAI}
              className="action-btn"
              title="Process with AI"
              disabled={processing}
            >
              {processing ? (
                <Loader className="spinner" size={16} />
              ) : (
                <Brain size={16} />
              )}
            </button>
          )}
        </div>
      </div>

      {/* Card Content */}
      <div className="receipt-card-content">
        {/* Amount */}
        {localReceipt.extracted_data?.total_amount && (
          <div className="receipt-amount">
            <DollarSign size={20} />
            <span className="amount">
              {formatCurrency(localReceipt.extracted_data.total_amount)}
            </span>
            {localReceipt.extracted_data.confidence_score && (
              <span className="confidence-score" title="AI Confidence Score">
                {Math.round(localReceipt.extracted_data.confidence_score * 100)}%
              </span>
            )}
          </div>
        )}

        {/* Details */}
        <div className="receipt-details">
          <div className="detail-item">
            <Calendar size={16} />
            <span>
              {localReceipt.extracted_data?.receipt_date || formatDate(localReceipt.created_at)}
            </span>
          </div>
          
          {localReceipt.extracted_data?.merchant_address && (
            <div className="detail-item">
              <MapPin size={16} />
              <span>{localReceipt.extracted_data.merchant_address}</span>
            </div>
          )}
          
          <div className="detail-item">
            <FileText size={16} />
            <span>{getFileType()}</span>
          </div>

          {/* File size info */}
          <div className="detail-item">
            <FileText size={16} />
            <span>
              {localReceipt.file_metadata?.file_size ? 
                `${(localReceipt.file_metadata.file_size / 1024).toFixed(1)} KB` : 
                'Unknown size'
              }
            </span>
          </div>
        </div>

        {/* Items Preview */}
        {localReceipt.extracted_data?.items && localReceipt.extracted_data.items.length > 0 && (
          <div className="items-preview">
            <h4>Items ({localReceipt.extracted_data.items.length})</h4>
            <div className="items-list">
              {localReceipt.extracted_data.items.slice(0, 3).map((item, index) => (
                <div key={index} className="item">
                  <span className="item-name">{item.name}</span>
                  {item.total_price && (
                    <span className="item-price">{formatCurrency(item.total_price)}</span>
                  )}
                </div>
              ))}
              {localReceipt.extracted_data.items.length > 3 && (
                <div className="more-items">
                  +{localReceipt.extracted_data.items.length - 3} more items
                </div>
              )}
            </div>
          </div>
        )}

        {/* Processing Status */}
        {localReceipt.status === 'uploaded' && (
          <div className="processing-notice">
            <Brain size={16} />
            <span>Ready for AI processing</span>
            <button 
              onClick={handleProcessWithAI}
              className="process-btn"
              disabled={processing}
            >
              {processing ? 'Processing...' : 'Extract Data'}
            </button>
          </div>
        )}
        
        {localReceipt.status === 'processing' && (
          <div className="processing-notice">
            <Loader className="spinner small" size={16} />
            <span>AI is extracting data...</span>
          </div>
        )}

        {localReceipt.status === 'processed' && (
          <div className="processing-notice success">
            <CheckCircle size={16} />
            <span>✨ Data extracted successfully!</span>
          </div>
        )}

        {localReceipt.status === 'error' && (
          <div className="processing-notice error">
            <AlertTriangle size={16} />
            <span>⚠️ Processing failed</span>
            <button 
              onClick={handleProcessWithAI}
              className="retry-btn"
              disabled={processing}
            >
              Retry
            </button>
          </div>
        )}

        {/* Debug info in development */}
        {process.env.NODE_ENV === 'development' && (
          <div style={{ 
            fontSize: '10px', 
            background: '#f0f0f0', 
            padding: '5px', 
            marginTop: '10px',
            borderRadius: '4px'
          }}>
            <strong>Debug:</strong> ID: {localReceipt.id}, 
            Status: {localReceipt.status}, 
            File: {getFileName()}
            {localReceipt.extracted_data && (
              <span>, Confidence: {Math.round((localReceipt.extracted_data.confidence_score || 0) * 100)}%</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ReceiptCard;
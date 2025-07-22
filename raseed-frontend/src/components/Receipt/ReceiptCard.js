// src/components/Receipt/ReceiptCard.js - Complete Update with Auto Wallet Integration
import React, { useState } from 'react';
import { 
  Calendar, DollarSign, MapPin, FileText, Eye, Download, Brain, 
  Loader, CheckCircle, AlertTriangle, CreditCard, ExternalLink, 
  Clock, Zap 
} from 'lucide-react';
import { receiptService } from '../../services/receiptService';
import WalletButton from './WalletButton';

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
        const updatedReceipt = {
          ...localReceipt,
          status: 'processed',
          extracted_data: result.extracted_data
        };

        // Handle auto-generated wallet pass
        if (result.wallet_pass) {
          updatedReceipt.wallet_pass = result.wallet_pass;
          
          if (result.wallet_pass.auto_generated) {
            console.log('🎫✨ Wallet pass auto-generated:', result.wallet_pass);
          } else {
            console.log('⚠️ Auto wallet generation failed:', result.wallet_pass.error);
          }
        }

        setLocalReceipt(updatedReceipt);
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

  const handleAddToWallet = () => {
    if (localReceipt.wallet_pass?.save_url) {
      console.log('🔗 Opening wallet save URL:', localReceipt.wallet_pass.save_url);
      window.open(localReceipt.wallet_pass.save_url, '_blank', 'noopener,noreferrer');
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
          <div className="status-badges">
            <span className={`status-badge status-${getStatusColor(localReceipt.status)}`}>
              {localReceipt.status}
            </span>
            {/* Auto-generated wallet pass indicator */}
            {localReceipt.wallet_pass?.auto_generated && (
              <span className="status-badge status-wallet">
                <Zap size={12} />
                Auto Pass
              </span>
            )}
          </div>
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

        {/* STEP 3: Wallet Pass Section */}
        {localReceipt.status === 'processed' && localReceipt.extracted_data && (
          <div className="receipt-wallet-section">
            <div className="wallet-section-header">
              <CreditCard size={16} />
              <span>Google Wallet Pass</span>
              <span className="step-badge">Step 3</span>
            </div>
            
            {/* Auto-Generated Wallet Pass */}
            {localReceipt.wallet_pass?.auto_generated ? (
              <div className="wallet-auto-generated">
                <div className="auto-generation-notice">
                  <Zap size={16} />
                  <span>✨ Wallet pass auto-generated!</span>
                  <span className="auto-timestamp">
                    <Clock size={12} />
                    {localReceipt.wallet_pass.generation_timestamp ? 
                      new Date(localReceipt.wallet_pass.generation_timestamp).toLocaleTimeString() : 
                      'Just now'
                    }
                  </span>
                </div>
                
                <button 
                  onClick={handleAddToWallet}
                  className="wallet-btn success auto-generated"
                >
                  <CheckCircle size={16} />
                  <span>Add to Google Wallet</span>
                  <ExternalLink size={14} />
                </button>
                
                <div className="wallet-info">
                  <p>Pass created automatically after AI processing</p>
                  <small>Object ID: {localReceipt.wallet_pass.wallet_object_id}</small>
                </div>
              </div>
            ) : localReceipt.wallet_pass?.error ? (
              /* Auto-generation failed, show manual option */
              <div className="wallet-auto-failed">
                <div className="auto-generation-error">
                  <AlertTriangle size={16} />
                  <span>Auto-generation failed: {localReceipt.wallet_pass.error}</span>
                </div>
                
                {localReceipt.wallet_pass.manual_creation_available && (
                  <div className="manual-fallback">
                    <p>You can still create a wallet pass manually:</p>
                    <WalletButton receipt={localReceipt} />
                  </div>
                )}
              </div>
            ) : (
              /* No auto-generation attempted, show manual creation */
              <div className="wallet-manual-creation">
                <WalletButton receipt={localReceipt} />
              </div>
            )}
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
            {localReceipt.wallet_pass && (
              <span>, Wallet: {localReceipt.wallet_pass.auto_generated ? 'Auto' : 'Manual'}</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ReceiptCard;
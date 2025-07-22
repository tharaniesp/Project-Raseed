// src/components/Receipt/WalletButton.js
import React, { useState } from 'react';
import { CreditCard, Loader, ExternalLink, CheckCircle, AlertTriangle } from 'lucide-react';
import { receiptService } from '../../services/receiptService';

const WalletButton = ({ receipt }) => {
  const [generating, setGenerating] = useState(false);
  const [walletData, setWalletData] = useState(null);
  const [error, setError] = useState(null);

  const handleGeneratePass = async () => {
    setGenerating(true);
    setError(null);
    
    try {
      console.log('🎫 Generating wallet pass for receipt:', receipt.id);
      
      const result = await receiptService.generateWalletPass(receipt.id);
      console.log('✅ Wallet pass generation result:', result);
      
      if (result.success) {
        setWalletData(result);
        console.log('🎉 Wallet pass generated successfully!');
      } else {
        setError(result.error || 'Failed to generate wallet pass');
      }
    } catch (err) {
      console.error('❌ Wallet pass generation failed:', err);
      setError(err.message || 'Network error occurred');
    } finally {
      setGenerating(false);
    }
  };

  const handleAddToWallet = () => {
    if (walletData?.save_url) {
      console.log('🔗 Opening wallet save URL:', walletData.save_url);
      window.open(walletData.save_url, '_blank', 'noopener,noreferrer');
    }
  };

  // Check if receipt has required data for wallet pass
  const canGeneratePass = receipt.extracted_data && 
                         receipt.status === 'processed' && 
                         receipt.extracted_data.merchant_name;

  if (!canGeneratePass) {
    return (
      <div className="wallet-button-container">
        <button className="wallet-btn disabled" disabled>
          <CreditCard size={16} />
          <span>Process with AI first</span>
        </button>
        <p className="wallet-help-text">
          Receipt must be processed with AI before creating wallet pass
        </p>
      </div>
    );
  }

  return (
    <div className="wallet-button-container">
      {!walletData ? (
        <button 
          onClick={handleGeneratePass}
          disabled={generating}
          className={`wallet-btn ${generating ? 'generating' : ''}`}
        >
          {generating ? (
            <>
              <Loader className="spinner" size={16} />
              <span>Creating Pass...</span>
            </>
          ) : (
            <>
              <CreditCard size={16} />
              <span>Create Wallet Pass</span>
            </>
          )}
        </button>
      ) : (
        <div className="wallet-success">
          <button 
            onClick={handleAddToWallet}
            className="wallet-btn success"
          >
            <CheckCircle size={16} />
            <span>Add to Google Wallet</span>
            <ExternalLink size={14} />
          </button>
          
          <div className="wallet-info">
            <p>✅ Wallet pass created successfully!</p>
            <small>Object ID: {walletData.wallet_object_id}</small>
          </div>
        </div>
      )}

      {error && (
        <div className="wallet-error">
          <AlertTriangle size={16} />
          <span>{error}</span>
          <button 
            onClick={handleGeneratePass}
            className="retry-btn"
            disabled={generating}
          >
            Retry
          </button>
        </div>
      )}

      {/* Debug info in development */}
      {process.env.NODE_ENV === 'development' && (
        <div className="wallet-debug">
          <details>
            <summary>Debug Info</summary>
            <pre>{JSON.stringify({
              receiptId: receipt.id,
              hasExtractedData: !!receipt.extracted_data,
              merchantName: receipt.extracted_data?.merchant_name,
              status: receipt.status,
              canGeneratePass,
              walletData,
              error
            }, null, 2)}</pre>
          </details>
        </div>
      )}
    </div>
  );
};

export default WalletButton;
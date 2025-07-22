// src/services/receiptService.js
import ApiService from './api';

export const receiptService = {
  // Upload receipt
  async uploadReceipt(file, onProgress) {
    const formData = new FormData();
    formData.append('file', file);

    // Simulate progress for demo (real progress needs different approach)
    if (onProgress) {
      const interval = setInterval(() => {
        onProgress(Math.min(90, Math.random() * 100));
      }, 100);
      
      setTimeout(() => {
        clearInterval(interval);
        onProgress(100);
      }, 1000);
    }

    return ApiService.post('/api/upload-receipt', formData);
  },

  // Get all receipts
  async getReceipts(limit = 10, offset = 0) {
    return ApiService.get(`/api/receipts?limit=${limit}&offset=${offset}`);
  },

  // Get single receipt
  async getReceipt(receiptId) {
    return ApiService.get(`/api/receipts/${receiptId}`);
  },

  // Process receipt with AI (Step 2)
  async processReceipt(receiptId) {
    return ApiService.post(`/api/receipts/${receiptId}/process`);
  },

  // Get processing status (Step 2)
  async getProcessingStatus(receiptId) {
    return ApiService.get(`/api/receipts/${receiptId}/processing-status`);
  },

  // Generate wallet pass (Step 3)
  async generateWalletPass(receiptId) {
    console.log('📱 Calling wallet pass API for receipt:', receiptId);
    try {
      const result = await ApiService.post(`/api/receipts/${receiptId}/generate-wallet-pass`);
      console.log('📱 Wallet pass API response:', result);
      return result;
    } catch (error) {
      console.error('❌ Wallet pass API error:', error);
      throw error;
    }
  },

  // Get wallet pass status (Step 3)
  async getWalletStatus(receiptId) {
    return ApiService.get(`/api/receipts/${receiptId}/wallet-status`);
  },

  // Test wallet service configuration
  async testWalletService() {
    return ApiService.get('/api/wallet/test');
  },

  // Natural language query (Step 4)
  async queryReceipts(query) {
    return ApiService.post('/api/query', { query });
  },

  // Health check
  async healthCheck() {
    return ApiService.get('/health');
  }
};

export const uploadReceipt = receiptService.uploadReceipt;
export default receiptService;
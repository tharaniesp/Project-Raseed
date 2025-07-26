// src/services/receiptService.js - Enhanced with Step 4 Natural Language Query Methods
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
  async getReceipts(limit = 20, offset = 0) {
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

  // ================================
  // STEP 4: NATURAL LANGUAGE QUERIES
  // ================================

  // Process natural language query (Step 4 - Main Feature)
  async processNaturalLanguageQuery(request) {
    console.log('🔍 Processing natural language query:', request.query);
    try {
      const result = await ApiService.post('/api/query', request);
      console.log('✅ Query processed:', result);
      return result;
    } catch (error) {
      console.error('❌ Query processing error:', error);
      throw error;
    }
  },

  // Create wallet pass from query response (Step 4)
  async createWalletPassFromQuery(request) {
    console.log('🎫 Creating wallet pass from query:', request.query_id);
    try {
      const result = await ApiService.post('/api/query/create-wallet-pass', request);
      console.log('✅ Wallet pass created from query:', result);
      return result;
    } catch (error) {
      console.error('❌ Wallet pass creation error:', error);
      throw error;
    }
  },

  // Generate detailed shopping list (Step 4)
  async generateShoppingList(query, userId = null) {
    console.log('🛒 Generating shopping list for:', query);
    try {
      const result = await ApiService.post('/api/query/shopping-list', {
        query: query,
        user_id: userId
      });
      console.log('✅ Shopping list generated:', result);
      return result;
    } catch (error) {
      console.error('❌ Shopping list generation error:', error);
      throw error;
    }
  },

  // Get query statistics (Step 4)
  async getQueryStatistics() {
    try {
      const result = await ApiService.get('/api/query/statistics');
      console.log('📊 Query statistics:', result);
      return result;
    } catch (error) {
      console.error('❌ Statistics error:', error);
      throw error;
    }
  },

  // Get Vertex AI status and configuration (Step 4)
  async getVertexAiStatus() {
    try {
      const result = await ApiService.get('/api/vertex-ai/status');
      console.log('🤖 Vertex AI status:', result);
      return result;
    } catch (error) {
      console.error('❌ Vertex AI status error:', error);
      throw error;
    }
  },

  // ================================
  // UTILITY METHODS
  // ================================

  // Health check
  async healthCheck() {
    return ApiService.get('/health');
  },

  // Test all Step 4 features
  async testStep4Features() {
    console.log('🧪 Testing Step 4 features...');
    
    const tests = [];
    
    try {
      // Test 1: Health check
      const health = await this.healthCheck();
      tests.push({ name: 'Health Check', status: 'passed', data: health });
    } catch (error) {
      tests.push({ name: 'Health Check', status: 'failed', error: error.message });
    }
    
    try {
      // Test 2: Query statistics
      const stats = await this.getQueryStatistics();
      tests.push({ name: 'Query Statistics', status: 'passed', data: stats });
    } catch (error) {
      tests.push({ name: 'Query Statistics', status: 'failed', error: error.message });
    }
    
    try {
      // Test 3: Vertex AI status
      const vertexStatus = await this.getVertexAiStatus();
      tests.push({ name: 'Vertex AI Status', status: 'passed', data: vertexStatus });
    } catch (error) {
      tests.push({ name: 'Vertex AI Status', status: 'failed', error: error.message });
    }
    
    try {
      // Test 4: Sample query
      const queryResult = await this.processNaturalLanguageQuery({
        query: "What can I cook with chicken?",
        user_id: "test_user"
      });
      tests.push({ name: 'Sample Query', status: 'passed', data: queryResult });
    } catch (error) {
      tests.push({ name: 'Sample Query', status: 'failed', error: error.message });
    }
    
    console.log('🧪 Step 4 test results:', tests);
    return tests;
  }
};

// Legacy exports for backward compatibility
export const uploadReceipt = receiptService.uploadReceipt;
export default receiptService;
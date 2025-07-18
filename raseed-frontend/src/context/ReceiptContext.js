// src/context/ReceiptContext.js
import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { receiptService } from '../services/receiptService';

// Initial state
const initialState = {
  receipts: [],
  currentReceipt: null,
  loading: false,
  error: null,
  backendStatus: 'unknown',
  totalReceipts: 0
};

// Action types
const ACTIONS = {
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  SET_RECEIPTS: 'SET_RECEIPTS',
  ADD_RECEIPT: 'ADD_RECEIPT',
  UPDATE_RECEIPT: 'UPDATE_RECEIPT',
  SET_CURRENT_RECEIPT: 'SET_CURRENT_RECEIPT',
  SET_BACKEND_STATUS: 'SET_BACKEND_STATUS',
  CLEAR_ERROR: 'CLEAR_ERROR'
};

// Reducer
function receiptReducer(state, action) {
  console.log('🔄 ReceiptContext Action:', action.type, action.payload);
  
  switch (action.type) {
    case ACTIONS.SET_LOADING:
      return { ...state, loading: action.payload };
    
    case ACTIONS.SET_ERROR:
      console.error('❌ ReceiptContext Error:', action.payload);
      return { ...state, error: action.payload, loading: false };
    
    case ACTIONS.CLEAR_ERROR:
      return { ...state, error: null };
    
    case ACTIONS.SET_RECEIPTS:
      console.log('📋 Setting receipts:', action.payload);
      return { 
        ...state, 
        receipts: action.payload.receipts || [],
        totalReceipts: action.payload.total || action.payload.receipts?.length || 0,
        loading: false 
      };
    
    case ACTIONS.ADD_RECEIPT:
      console.log('➕ Adding receipt:', action.payload);
      return { 
        ...state, 
        receipts: [action.payload, ...state.receipts],
        totalReceipts: state.totalReceipts + 1
      };
    
    case ACTIONS.UPDATE_RECEIPT:
      return {
        ...state,
        receipts: state.receipts.map(receipt =>
          receipt.id === action.payload.id ? action.payload : receipt
        ),
        currentReceipt: state.currentReceipt?.id === action.payload.id 
          ? action.payload 
          : state.currentReceipt
      };
    
    case ACTIONS.SET_CURRENT_RECEIPT:
      return { ...state, currentReceipt: action.payload };
    
    case ACTIONS.SET_BACKEND_STATUS:
      console.log('🔗 Backend status:', action.payload);
      return { ...state, backendStatus: action.payload };
    
    default:
      return state;
  }
}

// Create context
const ReceiptContext = createContext();

// Provider component
export function ReceiptProvider({ children }) {
  const [state, dispatch] = useReducer(receiptReducer, initialState);

  // Check backend status
  const checkBackendStatus = async () => {
    try {
      console.log('🔍 Checking backend status...');
      await receiptService.healthCheck();
      dispatch({ type: ACTIONS.SET_BACKEND_STATUS, payload: 'online' });
    } catch (error) {
      console.error('🔴 Backend health check failed:', error);
      dispatch({ type: ACTIONS.SET_BACKEND_STATUS, payload: 'offline' });
    }
  };

  // Load receipts
  const loadReceipts = async (limit = 10, offset = 0) => {
    try {
      console.log('📥 Loading receipts...', { limit, offset });
      dispatch({ type: ACTIONS.SET_LOADING, payload: true });
      
      const response = await receiptService.getReceipts(limit, offset);
      console.log('📨 API Response:', response);
      
      // 🔧 FIX: Handle different response formats
      let receiptsData;
      if (response.receipts) {
        // Standard API response format
        receiptsData = response;
      } else if (Array.isArray(response)) {
        // Direct array response
        receiptsData = { receipts: response, total: response.length };
      } else {
        // Unknown format
        console.warn('⚠️ Unexpected API response format:', response);
        receiptsData = { receipts: [], total: 0 };
      }
      
      dispatch({ type: ACTIONS.SET_RECEIPTS, payload: receiptsData });
    } catch (error) {
      console.error('❌ Load receipts error:', error);
      dispatch({ type: ACTIONS.SET_ERROR, payload: error.message });
    }
  };

  // Add receipt (from upload)
  const addReceipt = (receiptData) => {
    console.log('➕ Adding receipt to context:', receiptData);
    
    // Convert upload response to receipt format
    const receipt = {
      id: receiptData.receipt_id,
      download_url: receiptData.download_url,
      file_metadata: {
        original_filename: receiptData.metadata?.filename || receiptData.metadata?.original_filename,
        stored_filename: receiptData.metadata?.stored_filename,
        file_size: receiptData.metadata?.size || receiptData.metadata?.file_size,
        content_type: receiptData.metadata?.type || receiptData.metadata?.content_type,
        upload_date: new Date().toISOString()
      },
      status: 'uploaded',
      extracted_data: null,
      processing_error: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    
    console.log('🎯 Formatted receipt for context:', receipt);
    dispatch({ type: ACTIONS.ADD_RECEIPT, payload: receipt });
  };

  // Update receipt
  const updateReceipt = (receipt) => {
    dispatch({ type: ACTIONS.UPDATE_RECEIPT, payload: receipt });
  };

  // Set current receipt
  const setCurrentReceipt = async (receiptId) => {
    try {
      dispatch({ type: ACTIONS.SET_LOADING, payload: true });
      const receipt = await receiptService.getReceipt(receiptId);
      dispatch({ type: ACTIONS.SET_CURRENT_RECEIPT, payload: receipt });
    } catch (error) {
      dispatch({ type: ACTIONS.SET_ERROR, payload: error.message });
    }
  };

  // Clear error
  const clearError = () => {
    dispatch({ type: ACTIONS.CLEAR_ERROR });
  };

  // Check backend status on mount
  useEffect(() => {
    console.log('🚀 ReceiptProvider initializing...');
    checkBackendStatus();
    loadReceipts();
  }, []);

  // Debug state changes
  useEffect(() => {
    console.log('📊 ReceiptContext State:', {
      receiptsCount: state.receipts.length,
      loading: state.loading,
      error: state.error,
      backendStatus: state.backendStatus,
      totalReceipts: state.totalReceipts
    });
  }, [state]);

  const value = {
    ...state,
    actions: {
      loadReceipts,
      addReceipt,
      updateReceipt,
      setCurrentReceipt,
      clearError,
      checkBackendStatus
    }
  };

  return (
    <ReceiptContext.Provider value={value}>
      {children}
    </ReceiptContext.Provider>
  );
}

// Custom hook
export function useReceipt() {
  const context = useContext(ReceiptContext);
  if (!context) {
    throw new Error('useReceipt must be used within a ReceiptProvider');
  }
  return context;
}

export default ReceiptContext;
// src/pages/QueryPage.js - Improved UI with Clean Dropdowns
import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown'; 
import { 
  MessageSquare, Send, Lightbulb, Globe, Brain, CreditCard, 
  Loader, Mic, MicOff, Languages, ChevronDown,
  ShoppingCart, ChefHat, Package, TrendingUp, ExternalLink,
  Sparkles, Zap
} from 'lucide-react';
import { receiptService } from '../services/receiptService';

const QueryPage = () => {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState('auto');
  const [isListening, setIsListening] = useState(false);
  const [vertexAiStatus, setVertexAiStatus] = useState(null);
  const [queryStats, setQueryStats] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('cooking');
  const messagesEndRef = useRef(null);

  // Language options
  const languages = [
    { code: 'auto', name: 'Auto-detect', flag: '🌐' },
    { code: 'en', name: 'English', flag: '🇺🇸' },
    { code: 'es', name: 'Spanish', flag: '🇪🇸' },
    { code: 'fr', name: 'French', flag: '🇫🇷' },
    { code: 'de', name: 'German', flag: '🇩🇪' },
    { code: 'it', name: 'Italian', flag: '🇮🇹' },
    { code: 'pt', name: 'Portuguese', flag: '🇵🇹' },
    { code: 'zh', name: 'Chinese', flag: '🇨🇳' },
  ];

  // Sample queries organized by category
  const queryCategories = {
    cooking: {
      icon: ChefHat,
      color: '#f59e0b',
      label: 'Cooking & Recipes',
      queries: [
        "What can I cook with chicken and rice?",
        "¿Qué puedo cocinar con pollo y arroz?",
        "Qu'est-ce que je peux cuisiner avec du poulet?",
        "Suggest a recipe using ingredients I bought this week"
      ]
    },
    shopping: {
      icon: ShoppingCart,
      color: '#10b981',
      label: 'Shopping Lists',
      queries: [
        "What ingredients do I need to buy to make pasta?",
        "¿Qué necesito comprar para hacer gazpacho?",
        "Create a shopping list for making tacos",
        "I need to buy ingredients for chicken curry"
      ]
    },
    inventory: {
      icon: Package,
      color: '#3b82f6',
      label: 'Inventory Check',
      queries: [
        "Do I have enough laundry detergent for the week?",
        "Check if I have milk and eggs",
        "What food items am I running low on?",
        "How much bread do I have left?"
      ]
    },
    spending: {
      icon: TrendingUp,
      color: '#8b5cf6',
      label: 'Spending Analysis',
      queries: [
        "How much did I spend on groceries this month?",
        "What's my average weekly food spending?",
        "Show my spending pattern for household items",
        "What was my biggest purchase this week?"
      ]
    }
  };

  // Load initial data
  useEffect(() => {
    loadVertexAiStatus();
    loadQueryStatistics();
    
    // Add welcome message
    setMessages([{
      type: 'system',
      content: '🌟 Welcome to Project Raseed AI Assistant! Ask me anything about your receipts in any language.',
      timestamp: new Date(),
      confidence: 1.0,
      language: 'en'
    }]);
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadVertexAiStatus = async () => {
    try {
      const response = await receiptService.getVertexAiStatus();
      setVertexAiStatus(response);
    } catch (error) {
      console.error('Failed to load Vertex AI status:', error);
    }
  };

  const loadQueryStatistics = async () => {
    try {
      const response = await receiptService.getQueryStatistics();
      setQueryStats(response);
    } catch (error) {
      console.error('Failed to load query statistics:', error);
    }
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!query.trim() || loading) return;

    const userMessage = {
      type: 'user',
      content: query,
      timestamp: new Date(),
      language: selectedLanguage === 'auto' ? 'unknown' : selectedLanguage
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await receiptService.processNaturalLanguageQuery({
        query: query,
        language: selectedLanguage === 'auto' ? null : selectedLanguage,
        user_id: 'current_user'
      });

      const aiMessage = {
        type: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        confidence: response.confidence,
        queryType: response.query_type,
        detectedLanguage: response.detected_language,
        sources: response.sources,
        actionableItems: response.actionable_items || [],
        canCreateWalletPass: response.can_create_wallet_pass,
        suggestedActions: response.suggested_actions || []
      };

      setMessages(prev => [...prev, aiMessage]);
      loadQueryStatistics();
      
    } catch (error) {
      const errorMessage = {
        type: 'error',
        content: `Sorry, I encountered an error: ${error.message}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      setQuery('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleSampleQuery = (sampleQuery) => {
    setQuery(sampleQuery);
  };

  const handleCreateWalletPass = async (message) => {
    if (!message.suggestedActions) return;

    const queryIdAction = message.suggestedActions.find(action => 
      action.includes('Query ID:')
    );
    
    if (!queryIdAction) return;

    const queryId = queryIdAction.match(/Query ID: ([^)]+)/)?.[1];
    if (!queryId) return;

    try {
      const result = await receiptService.createWalletPassFromQuery({
        query_id: queryId,
        pass_title: `Shopping List - ${message.queryType}`
      });

      if (result.success) {
        const successMessage = {
          type: 'system',
          content: `🎫 Wallet pass created successfully! Open the link to add to Google Wallet.`,
          timestamp: new Date(),
          walletPass: {
            saveUrl: result.save_url,
            objectId: result.wallet_object_id,
            itemsCount: result.items_count
          }
        };
        setMessages(prev => [...prev, successMessage]);
      }
    } catch (error) {
      console.error('Failed to create wallet pass:', error);
    }
  };

  const startVoiceInput = () => {
    if ('webkitSpeechRecognition' in window) {
      const recognition = new window.webkitSpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = selectedLanguage === 'auto' ? 'en-US' : `${selectedLanguage}-${selectedLanguage.toUpperCase()}`;

      recognition.onstart = () => setIsListening(true);
      recognition.onend = () => setIsListening(false);
      
      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setQuery(transcript);
      };

      recognition.start();
    }
  };

  const getQueryTypeIcon = (type) => {
    switch (type) {
      case 'cooking_suggestions': return <ChefHat size={16} />;
      case 'shopping_list': return <ShoppingCart size={16} />;
      case 'inventory_check': return <Package size={16} />;
      case 'spending_analysis': return <TrendingUp size={16} />;
      default: return <MessageSquare size={16} />;
    }
  };

  const getQueryTypeColor = (type) => {
    switch (type) {
      case 'cooking_suggestions': return '#f59e0b';
      case 'shopping_list': return '#10b981';
      case 'inventory_check': return '#3b82f6';
      case 'spending_analysis': return '#8b5cf6';
      default: return '#6b7280';
    }
  };

  const currentCategory = queryCategories[selectedCategory];
  const IconComponent = currentCategory.icon;

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Brain size={28} />
          AI Assistant
          <span style={{ 
            background: 'linear-gradient(135deg, #10b981, #059669)',
            color: 'white',
            fontSize: '0.7rem',
            padding: '0.2rem 0.6rem',
            borderRadius: '12px',
            fontWeight: '700',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            marginLeft: '0.5rem'
          }}>
            Step 4 Complete
          </span>
        </h1>
        <p className="page-description">
          Ask questions about your receipts in any language and get smart insights
        </p>
      </div>

      {/* Status Dashboard */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
        gap: '1rem', 
        marginBottom: '2rem' 
      }}>
        <div style={{
          background: 'linear-gradient(135deg, #faf5ff, #f3e8ff)',
          border: '1px solid #c084fc',
          borderRadius: '12px',
          padding: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '1rem'
        }}>
          <Brain style={{ color: '#8b5cf6' }} size={24} />
          <div>
            <h3 style={{ fontWeight: '600', color: '#111827', margin: '0 0 0.25rem 0' }}>Vertex AI</h3>
            <p style={{ fontSize: '0.875rem', color: '#6b7280', margin: 0 }}>
              {vertexAiStatus?.vertex_ai_status?.service_available ? '✅ Active' : '⚠️ Fallback Mode'}
            </p>
          </div>
        </div>

        <div style={{
          background: 'linear-gradient(135deg, #f0fdf4, #ecfdf5)',
          border: '1px solid #34d399',
          borderRadius: '12px',
          padding: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '1rem'
        }}>
          <Globe style={{ color: '#10b981' }} size={24} />
          <div>
            <h3 style={{ fontWeight: '600', color: '#111827', margin: '0 0 0.25rem 0' }}>Languages</h3>
            <p style={{ fontSize: '0.875rem', color: '#6b7280', margin: 0 }}>🌐 20+ Supported</p>
          </div>
        </div>

        <div style={{
          background: 'linear-gradient(135deg, #fffbeb, #fef3c7)',
          border: '1px solid #fbbf24',
          borderRadius: '12px',
          padding: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '1rem'
        }}>
          <Sparkles style={{ color: '#f59e0b' }} size={24} />
          <div>
            <h3 style={{ fontWeight: '600', color: '#111827', margin: '0 0 0.25rem 0' }}>Queries</h3>
            <p style={{ fontSize: '0.875rem', color: '#6b7280', margin: 0 }}>
              {queryStats?.statistics?.total_cached_queries || 0} processed
            </p>
          </div>
        </div>
      </div>

      {/* Language & Category Selectors */}
      <div style={{ 
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '1rem',
        marginBottom: '2rem'
      }}>
        {/* Language Selector */}
        <div style={{ 
          background: 'white', 
          borderRadius: '12px', 
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
          border: '1px solid #e5e7eb', 
          padding: '1.5rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <Languages size={20} style={{ color: '#6b7280' }} />
            <span style={{ fontWeight: '600', color: '#111827' }}>Language</span>
          </div>
          <div style={{ position: 'relative' }}>
            <select 
              value={selectedLanguage} 
              onChange={(e) => setSelectedLanguage(e.target.value)}
              style={{ 
                width: '100%',
                padding: '0.75rem 1rem',
                border: '1px solid #d1d5db', 
                borderRadius: '8px',
                background: 'white',
                fontSize: '1rem',
                cursor: 'pointer',
                appearance: 'none'
              }}
            >
              {languages.map(lang => (
                <option key={lang.code} value={lang.code}>
                  {lang.flag} {lang.name}
                </option>
              ))}
            </select>
            <ChevronDown 
              size={20} 
              style={{
                position: 'absolute',
                right: '1rem',
                top: '50%',
                transform: 'translateY(-50%)',
                pointerEvents: 'none',
                color: '#6b7280'
              }}
            />
          </div>
          <p style={{ fontSize: '0.8rem', color: '#6b7280', margin: '0.5rem 0 0 0' }}>
            Auto-translated and processed by Vertex AI
          </p>
        </div>

        {/* Query Category Selector */}
        <div style={{ 
          background: 'white', 
          borderRadius: '12px', 
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
          border: '1px solid #e5e7eb', 
          padding: '1.5rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <Lightbulb size={20} style={{ color: '#6b7280' }} />
            <span style={{ fontWeight: '600', color: '#111827' }}>Query Type</span>
          </div>
          <div style={{ position: 'relative' }}>
            <select 
              value={selectedCategory} 
              onChange={(e) => setSelectedCategory(e.target.value)}
              style={{ 
                width: '100%',
                padding: '0.75rem 1rem',
                border: '1px solid #d1d5db', 
                borderRadius: '8px',
                background: 'white',
                fontSize: '1rem',
                cursor: 'pointer',
                appearance: 'none'
              }}
            >
              {Object.entries(queryCategories).map(([key, category]) => (
                <option key={key} value={key}>
                  {category.label}
                </option>
              ))}
            </select>
            <ChevronDown 
              size={20} 
              style={{
                position: 'absolute',
                right: '1rem',
                top: '50%',
                transform: 'translateY(-50%)',
                pointerEvents: 'none',
                color: '#6b7280'
              }}
            />
          </div>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '0.5rem',
            marginTop: '0.75rem',
            padding: '0.5rem',
            background: '#f8fafc',
            borderRadius: '6px'
          }}>
            <IconComponent size={16} style={{ color: currentCategory.color }} />
            <span style={{ fontSize: '0.85rem', color: '#374151', fontWeight: '500' }}>
              {currentCategory.label}
            </span>
          </div>
        </div>
      </div>

      {/* Sample Queries for Selected Category */}
      <div style={{ 
        background: 'white', 
        borderRadius: '12px', 
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
        border: '1px solid #e5e7eb', 
        padding: '2rem', 
        marginBottom: '2rem' 
      }}>
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '0.75rem', 
          marginBottom: '1.5rem' 
        }}>
          <IconComponent size={24} style={{ color: currentCategory.color }} />
          <h3 style={{ fontSize: '1.25rem', fontWeight: '600', margin: 0, color: '#111827' }}>
            {currentCategory.label} Examples
          </h3>
        </div>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
          {currentCategory.queries.map((q, index) => (
            <button
              key={index}
              style={{
                textAlign: 'left',
                padding: '1rem',
                fontSize: '0.9rem',
                background: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                position: 'relative'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = '#f1f5f9';
                e.target.style.borderColor = currentCategory.color;
                e.target.style.transform = 'translateY(-1px)';
                e.target.style.boxShadow = `0 4px 12px ${currentCategory.color}20`;
              }}
              onMouseLeave={(e) => {
                e.target.style.background = '#f8fafc';
                e.target.style.borderColor = '#e2e8f0';
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = 'none';
              }}
              onClick={() => handleSampleQuery(q)}
            >
              <div style={{ 
                display: 'flex', 
                alignItems: 'flex-start', 
                gap: '0.5rem' 
              }}>
                <span style={{ 
                  fontSize: '1rem',
                  lineHeight: '1.5',
                  color: '#374151'
                }}>
                  "{q}"
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Chat Interface */}
      <div style={{ 
        background: 'white', 
        borderRadius: '12px', 
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
        border: '1px solid #e5e7eb', 
        overflow: 'hidden' 
      }}>
        {/* Messages */}
        <div style={{ 
          height: '28rem', 
          overflowY: 'auto', 
          padding: '1.5rem', 
          display: 'flex', 
          flexDirection: 'column', 
          gap: '1rem',
          background: '#fafafa'
        }}>
          {messages.map((message, index) => (
            <div key={index} style={{ 
              display: 'flex', 
              justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start' 
            }}>
              <div style={{
                maxWidth: '75%',
                padding: '1rem 1.25rem',
                borderRadius: '16px',
                background: message.type === 'user' 
                  ? 'linear-gradient(135deg, #3b82f6, #2563eb)' 
                  : message.type === 'error'
                  ? '#fef2f2'
                  : message.type === 'system'
                  ? 'linear-gradient(135deg, #f0fdf4, #dcfce7)'
                  : 'white',
                color: message.type === 'user' 
                  ? 'white' 
                  : message.type === 'error'
                  ? '#991b1b'
                  : message.type === 'system'
                  ? '#166534'
                  : '#374151',
                border: message.type === 'user' 
                  ? 'none'
                  : message.type === 'error' 
                  ? '1px solid #fecaca' 
                  : message.type === 'system'
                  ? '1px solid #bbf7d0'
                  : '1px solid #e5e7eb',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)'
              }}>
                <div style={{ fontSize: '0.95rem', lineHeight: '1.5' }}><ReactMarkdown>{message.content}</ReactMarkdown></div>
                
                {/* AI Response Metadata */}
                {message.type === 'assistant' && (
                  <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '0.5rem', 
                      fontSize: '0.8rem', 
                      opacity: 0.8,
                      background: '#f8fafc',
                      padding: '0.5rem',
                      borderRadius: '6px'
                    }}>
                      {getQueryTypeIcon(message.queryType)}
                      <span style={{ color: getQueryTypeColor(message.queryType), fontWeight: '500' }}>
                        {message.queryType?.replace('_', ' ')}
                      </span>
                      <span>•</span>
                      <span>🌐 {message.detectedLanguage}</span>
                      <span>•</span>
                      <span>📊 {Math.round(message.confidence * 100)}%</span>
                    </div>
                    
                    {/* Actionable Items */}
                    {message.actionableItems && message.actionableItems.length > 0 && (
                      <div style={{ 
                        background: 'rgba(16, 185, 129, 0.1)', 
                        borderRadius: '8px', 
                        padding: '0.75rem',
                        border: '1px solid rgba(16, 185, 129, 0.2)'
                      }}>
                        <div style={{ fontWeight: '600', marginBottom: '0.5rem', color: '#059669' }}>
                          🛒 Shopping Items ({message.actionableItems.length})
                        </div>
                        {message.actionableItems.map((item, i) => (
                          <div key={i} style={{ 
                            fontSize: '0.8rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            marginBottom: '0.25rem'
                          }}>
                            <span style={{
                              background: '#10b981',
                              color: 'white',
                              padding: '0.1rem 0.4rem',
                              borderRadius: '12px',
                              fontSize: '0.7rem',
                              fontWeight: '600',
                              minWidth: '2rem',
                              textAlign: 'center'
                            }}>
                              {item.quantity}x
                            </span>
                            <span style={{ flex: 1 }}>{item.name}</span>
                            <span style={{
                              background: '#f3f4f6',
                              color: '#6b7280',
                              padding: '0.1rem 0.4rem',
                              borderRadius: '12px',
                              fontSize: '0.7rem',
                              textTransform: 'uppercase',
                              fontWeight: '500'
                            }}>
                              {item.category}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                    
                    {/* Wallet Pass Button */}
                    {message.canCreateWalletPass && (
                      <button
                        onClick={() => handleCreateWalletPass(message)}
                        style={{
                          width: '100%',
                          marginTop: '0.5rem',
                          background: 'linear-gradient(135deg, #1a73e8, #4285f4)',
                          color: 'white',
                          padding: '0.75rem 1rem',
                          borderRadius: '8px',
                          fontSize: '0.85rem',
                          fontWeight: '600',
                          border: 'none',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '0.5rem',
                          transition: 'all 0.2s',
                          boxShadow: '0 2px 8px rgba(26, 115, 232, 0.3)'
                        }}
                        onMouseEnter={(e) => {
                          e.target.style.background = 'linear-gradient(135deg, #1557b0, #3367d6)';
                          e.target.style.transform = 'translateY(-1px)';
                          e.target.style.boxShadow = '0 4px 12px rgba(26, 115, 232, 0.4)';
                        }}
                        onMouseLeave={(e) => {
                          e.target.style.background = 'linear-gradient(135deg, #1a73e8, #4285f4)';
                          e.target.style.transform = 'translateY(0)';
                          e.target.style.boxShadow = '0 2px 8px rgba(26, 115, 232, 0.3)';
                        }}
                      >
                        <CreditCard size={16} />
                        Create Google Wallet Pass
                      </button>
                    )}
                  </div>
                )}

                {/* Wallet Pass Success Link */}
                {message.walletPass && (
                  <a
                    href={message.walletPass.saveUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      marginTop: '0.75rem',
                      background: 'linear-gradient(135deg, #10b981, #059669)',
                      color: 'white',
                      padding: '0.75rem 1rem',
                      borderRadius: '8px',
                      fontSize: '0.85rem',
                      fontWeight: '600',
                      textDecoration: 'none',
                      transition: 'all 0.2s',
                      boxShadow: '0 2px 8px rgba(16, 185, 129, 0.3)'
                    }}
                  >
                    <ExternalLink size={16} />
                    Add to Google Wallet ({message.walletPass.itemsCount} items)
                  </a>
                )}
                
                <div style={{ fontSize: '0.75rem', opacity: 0.6, marginTop: '0.5rem' }}>
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
          
          {loading && (
            <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
              <div style={{
                background: 'white',
                border: '1px solid #e5e7eb',
                color: '#374151',
                padding: '1rem 1.25rem',
                borderRadius: '16px',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <Loader style={{ animation: 'spin 1s linear infinite' }} size={18} />
                  <span>AI is thinking...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Enhanced Input Section */}
        <div style={{ 
          borderTop: '1px solid #e5e7eb', 
          padding: '1.5rem',
          background: 'white'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ flex: 1, position: 'relative' }}>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask about your receipts in any language..."
                style={{
                  width: '100%',
                  border: '2px solid #e5e7eb',
                  borderRadius: '12px',
                  padding: '1rem 1.25rem',
                  paddingRight: '3rem',
                  outline: 'none',
                  fontSize: '1rem',
                  transition: 'border-color 0.2s'
                }}
                disabled={loading}
                onFocus={(e) => e.target.style.borderColor = '#3b82f6'}
                onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
              />
              {query && (
                <button
                  type="button"
                  onClick={() => setQuery('')}
                  style={{
                    position: 'absolute',
                    right: '1rem',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'none',
                    border: 'none',
                    color: '#9ca3af',
                    cursor: 'pointer',
                    fontSize: '1.5rem',
                    padding: '0.25rem'
                  }}
                >
                  ×
                </button>
              )}
            </div>
            
            <button
              type="button"
              onClick={startVoiceInput}
              style={{
                padding: '1rem',
                borderRadius: '12px',
                border: '2px solid #e5e7eb',
                background: isListening ? '#ef4444' : '#f8fafc',
                color: isListening ? 'white' : '#6b7280',
                cursor: 'pointer',
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
              disabled={loading}
              onMouseEnter={(e) => {
                if (!isListening && !loading) {
                  e.target.style.background = '#f1f5f9';
                  e.target.style.borderColor = '#3b82f6';
                }
              }}
              onMouseLeave={(e) => {
                if (!isListening && !loading) {
                  e.target.style.background = '#f8fafc';
                  e.target.style.borderColor = '#e5e7eb';
                }
              }}
            >
              {isListening ? <MicOff size={22} /> : <Mic size={22} />}
            </button>
            
            <button
              type="button"
              onClick={handleSubmit}
              disabled={loading || !query.trim()}
              style={{
                background: loading || !query.trim() 
                  ? '#9ca3af' 
                  : 'linear-gradient(135deg, #3b82f6, #2563eb)',
                color: 'white',
                padding: '1rem 1.5rem',
                borderRadius: '12px',
                border: 'none',
                cursor: loading || !query.trim() ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                fontSize: '1rem',
                fontWeight: '600',
                boxShadow: loading || !query.trim() 
                  ? 'none' 
                  : '0 2px 8px rgba(59, 130, 246, 0.3)'
              }}
              onMouseEnter={(e) => {
                if (!loading && query.trim()) {
                  e.target.style.background = 'linear-gradient(135deg, #2563eb, #1d4ed8)';
                  e.target.style.transform = 'translateY(-1px)';
                  e.target.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.4)';
                }
              }}
              onMouseLeave={(e) => {
                if (!loading && query.trim()) {
                  e.target.style.background = 'linear-gradient(135deg, #3b82f6, #2563eb)';
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = '0 2px 8px rgba(59, 130, 246, 0.3)';
                }
              }}
            >
              {loading ? (
                <>
                  <Loader style={{ animation: 'spin 1s linear infinite' }} size={20} />
                  Processing...
                </>
              ) : (
                <>
                  <Send size={20} />
                  Send
                </>
              )}
            </button>
          </div>
          
          {/* Quick Action Hints */}
          <div style={{ 
            marginTop: '1rem',
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
            fontSize: '0.85rem',
            color: '#6b7280'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Zap size={14} />
              <span>Press Enter to send</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Mic size={14} />
              <span>Click to use voice</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Globe size={14} />
              <span>Auto-translated</span>
            </div>
          </div>
        </div>
      </div>

      {/* Enhanced Features Footer */}
      <div style={{ 
        marginTop: '2rem', 
        background: 'linear-gradient(135deg, #eff6ff, #f3e8ff)', 
        borderRadius: '12px', 
        padding: '2rem', 
        border: '1px solid #c7d2fe',
        textAlign: 'center'
      }}>
        <h4 style={{ 
          fontWeight: '700', 
          color: '#111827', 
          marginBottom: '1rem',
          fontSize: '1.25rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.5rem'
        }}>
          <Sparkles size={24} />
          Powered by Vertex AI
        </h4>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
          gap: '1rem',
          fontSize: '0.9rem',
          color: '#6b7280'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Globe size={18} style={{ color: '#10b981' }} />
            <span>Multi-language support with automatic translation</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Brain size={18} style={{ color: '#8b5cf6' }} />
            <span>Smart query classification and contextual responses</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ShoppingCart size={18} style={{ color: '#f59e0b' }} />
            <span>Automatic shopping list generation</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <CreditCard size={18} style={{ color: '#3b82f6' }} />
            <span>Google Wallet pass creation</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QueryPage;
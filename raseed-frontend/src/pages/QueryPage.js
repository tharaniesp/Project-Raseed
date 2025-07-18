// src/pages/QueryPage.js
import React, { useState } from 'react';
import { MessageSquare, Send, Lightbulb } from 'lucide-react';
import { receiptService } from '../services/receiptService';

const QueryPage = () => {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([
    {
      type: 'system',
      content: 'Welcome! Once Step 4 is implemented, you can ask questions about your receipts in natural language.',
      timestamp: new Date()
    }
  ]);
  const [loading, setLoading] = useState(false);

  const sampleQueries = [
    "How much did I spend on groceries last month?",
    "What's my average weekly food spending?",
    "Do I have enough detergent left?",
    "Show me all receipts from Walmart",
    "What was my biggest purchase this week?"
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userMessage = {
      type: 'user',
      content: query,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await receiptService.queryReceipts(query);
      
      const aiMessage = {
        type: 'assistant',
        content: response.answer || 'This feature will be available in Step 4!',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      const errorMessage = {
        type: 'error',
        content: 'Unable to process query. This feature will be implemented in Step 4.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      setQuery('');
    }
  };

  const handleSampleQuery = (sampleQuery) => {
    setQuery(sampleQuery);
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Ask Questions</h1>
        <p className="page-description">
          Ask natural language questions about your receipts and spending patterns
        </p>
      </div>

      <div className="query-interface">
        {/* Sample Queries */}
        <div className="sample-queries">
          <h3>
            <Lightbulb size={20} />
            Try asking:
          </h3>
          <div className="sample-grid">
            {sampleQueries.map((sample, index) => (
              <button
                key={index}
                className="sample-query"
                onClick={() => handleSampleQuery(sample)}
              >
                "{sample}"
              </button>
            ))}
          </div>
        </div>

        {/* Chat Messages */}
        <div className="chat-container">
          <div className="messages">
            {messages.map((message, index) => (
              <div key={index} className={`message ${message.type}`}>
                <div className="message-content">
                  {message.content}
                </div>
                <div className="message-time">
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            ))}
            {loading && (
              <div className="message assistant">
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Query Input */}
          <form className="query-form" onSubmit={handleSubmit}>
            <div className="query-input-container">
              <MessageSquare size={20} />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask about your receipts..."
                className="query-input"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="send-button"
              >
                <Send size={18} />
              </button>
            </div>
          </form>
        </div>

        {/* Step 4 Preview */}
        <div className="feature-preview">
          <h4>🚀 Coming in Step 4</h4>
          <ul>
            <li>Natural language processing with Gemini Pro</li>
            <li>Smart insights and spending analysis</li>
            <li>Multi-language support</li>
            <li>Contextual recommendations</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default QueryPage;
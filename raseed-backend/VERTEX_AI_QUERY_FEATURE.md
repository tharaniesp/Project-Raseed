# Vertex AI Local Language Query Feature

## Overview

This feature enables users to make natural language queries about their receipts and purchases in their local language, and automatically generate Google Wallet passes for actionable responses like shopping lists.

## Features

- **Multi-Language Support**: Detect and process queries in various languages
- **Smart Query Classification**: Automatically categorize queries (cooking, shopping, inventory, spending analysis)
- **Receipt Data Integration**: Analyze purchase history from Firestore database
- **Actionable Responses**: Generate shopping lists and recommendations
- **Google Wallet Integration**: Create wallet passes for shopping lists
- **Vertex AI Agent Builder**: Leverage Google's conversational AI platform

## Setup Requirements

### 1. Google Cloud Configuration

```bash
# Ensure these are set in your environment or .env file
FIREBASE_PROJECT_ID=your-project-id
VERTEX_AI_LOCATION=global
VERTEX_AI_DATA_STORE_ID=raseed-receipts-datastore
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Required new packages:
- `google-cloud-discoveryengine==0.11.0`
- `google-cloud-dialogflow-cx==1.26.0`
- `langdetect==1.0.9`
- `googletrans==4.0.0`

### 3. Google Cloud Services

Enable these APIs in your Google Cloud Console:
- Vertex AI API
- Discovery Engine API
- Google Wallet API

## API Endpoints

### 1. Natural Language Query
```
POST /api/query
```

**Request Body:**
```json
{
    "query": "What can I cook with the food I bought from the last two weeks?",
    "user_id": "optional_user_id",
    "language": "en",  // Optional, auto-detected if not provided
    "context": {}      // Optional additional context
}
```

**Response:**
```json
{
    "answer": "Based on your recent purchases, you can make...",
    "confidence": 0.85,
    "query_type": "cooking_suggestions",
    "detected_language": "en",
    "sources": ["Recent receipts (15 items analyzed)"],
    "actionable_items": [
        {
            "name": "tomatoes",
            "quantity": "2",
            "category": "food",
            "estimated_price": 3.50,
            "priority": "normal"
        }
    ],
    "can_create_wallet_pass": true,
    "suggested_actions": [
        "Create wallet pass (Query ID: abc123)",
        "Save favorite recipes"
    ]
}
```

### 2. Create Wallet Pass from Query
```
POST /api/query/create-wallet-pass
```

**Request Body:**
```json
{
    "query_id": "abc123",
    "pass_title": "Weekly Shopping List",
    "custom_items": []  // Optional: Override items from query
}
```

**Response:**
```json
{
    "success": true,
    "wallet_object_id": "3388000000022971095.list_abc123",
    "save_url": "https://pay.google.com/gp/v/save/...",
    "class_id": "3388000000022971095.shopping_list_1234567890",
    "items_count": 5
}
```

### 3. Generate Shopping List
```
POST /api/query/shopping-list
```

**Request Body:**
```json
{
    "query": "What ingredients do I need to buy to make pasta?",
    "user_id": "optional_user_id"
}
```

**Response:**
```json
{
    "title": "Recipe Shopping List (4 ingredients)",
    "items": [
        {
            "name": "pasta",
            "quantity": "1 lb",
            "category": "food",
            "estimated_price": 2.50,
            "priority": "normal",
            "suggested_store": "Grocery Store",
            "notes": null
        }
    ],
    "total_estimated_cost": 15.75,
    "suggested_stores": ["Grocery Store"],
    "budget_friendly_alternatives": [
        "Consider store brands for basic food items"
    ]
}
```

### 4. Query Statistics
```
GET /api/query/statistics
```

**Response:**
```json
{
    "success": true,
    "statistics": {
        "total_cached_queries": 25,
        "used_for_wallet_passes": 8,
        "query_types": {
            "cooking_suggestions": 10,
            "shopping_list": 8,
            "inventory_check": 5,
            "spending_analysis": 2
        },
        "cache_utilization": "32.0%"
    },
    "vertex_ai_available": true,
    "wallet_service_available": true
}
```

## Supported Query Types

### 1. Cooking Suggestions
**Examples:**
- "What can I cook with chicken and rice?"
- "Suggest a recipe using ingredients I bought this week"
- "What dish can I make with the vegetables I have?"

**Response Features:**
- Recipe suggestions based on available ingredients
- Missing ingredient identification
- Step-by-step cooking instructions

### 2. Shopping Lists
**Examples:**
- "What do I need to buy for grocery shopping?"
- "Create a shopping list for making lasagna"
- "What ingredients am I missing for this recipe?"

**Response Features:**
- Structured shopping lists
- Quantity suggestions
- Store recommendations
- Google Wallet pass creation

### 3. Inventory Check
**Examples:**
- "Do I have enough milk for the week?"
- "Check if I have laundry detergent"
- "What food items am I running low on?"

**Response Features:**
- Inventory status based on recent purchases
- Quantity analysis
- Replacement suggestions

### 4. Spending Analysis
**Examples:**
- "How much did I spend on groceries this month?"
- "Show my spending pattern for household items"
- "What are my most expensive purchases?"

**Response Features:**
- Spending breakdowns
- Cost analysis
- Budget recommendations

## Multi-Language Support

The system automatically detects and processes queries in multiple languages:

### Supported Languages
- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Dutch (nl)
- And many more via Google Translate

### Language Processing Flow
1. **Detection**: Auto-detect query language using `langdetect`
2. **Translation**: Translate to English for processing if needed
3. **Processing**: Use English for AI analysis and data retrieval
4. **Response Translation**: Translate response back to user's language

### Example Multi-Language Queries

**Spanish:**
```json
{
    "query": "¿Qué puedo cocinar con la comida que compré la semana pasada?",
    "language": "es"
}
```

**French:**
```json
{
    "query": "Qu'est-ce que je peux cuisiner avec la nourriture que j'ai achetée?",
    "language": "fr"
}
```

## Google Wallet Pass Integration

### Shopping List Passes

When a query results in actionable items (shopping lists), the system can automatically create Google Wallet passes:

#### Pass Features
- **Title**: Descriptive title (e.g., "Shopping List (5 items)")
- **Items List**: Numbered list with quantities
- **Categories**: Item categorization
- **Estimated Total**: Cost estimation when available
- **Metadata**: Query ID, language, creation date

#### Pass Appearance
```
┌─────────────────────────────┐
│ 🛒 Shopping List            │
│ 5 items                     │
├─────────────────────────────┤
│ Items to Buy:               │
│ 1. 2x tomatoes (food)       │
│ 2. 1x bread (food)          │
│ 3. 1x milk (dairy)          │
│ 4. 1x pasta (food)          │
│ 5. 1x cheese (dairy)        │
├─────────────────────────────┤
│ Estimated Total: $15.75     │
└─────────────────────────────┘
```

## Configuration Options

### Environment Variables

```bash
# Vertex AI Configuration
VERTEX_AI_LOCATION=global
VERTEX_AI_DATA_STORE_ID=raseed-receipts-datastore
VERTEX_AI_AGENT_ID=optional_agent_id

# Language Settings
ENABLE_MULTI_LANGUAGE=true
DEFAULT_LANGUAGE=en
QUERY_CACHE_TIMEOUT=3600
MAX_QUERY_CACHE_SIZE=100

# Google Wallet
GOOGLE_WALLET_ISSUER_ID=your_issuer_id
AUTO_GENERATE_WALLET_PASS=true
```

### Customization Options

1. **Query Processing Timeout**: Adjust AI processing time limits
2. **Cache Settings**: Configure query caching behavior
3. **Language Support**: Enable/disable specific languages
4. **Wallet Pass Design**: Customize pass appearance and content

## Error Handling

### Common Errors and Solutions

1. **"Vertex AI Agent not available"**
   - Check FIREBASE_PROJECT_ID is set
   - Ensure Vertex AI API is enabled
   - Verify service account permissions

2. **"Language detection failed"**
   - Query may be too short
   - Mixed language queries not supported
   - Specify language explicitly in request

3. **"Wallet service not configured"**
   - Check GOOGLE_WALLET_ISSUER_ID
   - Verify service account has Wallet API permissions
   - Ensure Google Wallet API is enabled

4. **"No actionable items found"**
   - Query doesn't result in shopping list
   - Try more specific requests
   - Check recent receipt data availability

## Usage Examples

### Basic Cooking Query
```bash
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What can I cook with chicken and vegetables?",
    "user_id": "user123"
  }'
```

### Shopping List with Wallet Pass
```bash
# 1. Create query
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I need to buy ingredients for spaghetti carbonara",
    "user_id": "user123"
  }'

# 2. Create wallet pass (use query_id from response)
curl -X POST "http://localhost:8000/api/query/create-wallet-pass" \
  -H "Content-Type: application/json" \
  -d '{
    "query_id": "abc123",
    "pass_title": "Carbonara Ingredients"
  }'
```

### Multi-Language Query
```bash
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿Tengo suficiente detergente para la semana?",
    "language": "es",
    "user_id": "user123"
  }'
```

## Best Practices

1. **Query Specificity**: More specific queries yield better results
2. **Language Consistency**: Use consistent language throughout a session
3. **Error Handling**: Always check response status and handle errors gracefully
4. **Cache Management**: Implement query result caching on client side for better UX
5. **Wallet Pass Usage**: Only create wallet passes for actionable shopping lists

## Troubleshooting

### Debug Mode
Enable debug logging to troubleshoot issues:

```python
import logging
logging.getLogger('app.services.vertex_ai_agent_service').setLevel(logging.DEBUG)
```

### Health Checks
Use the statistics endpoint to monitor system health:

```bash
curl "http://localhost:8000/api/query/statistics"
```

### Logs to Monitor
- Query processing times
- Language detection accuracy
- Wallet pass creation success rates
- Cache hit/miss ratios 
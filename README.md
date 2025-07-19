# 🧾 Project Raseed - AI-Powered Receipt Management System

An intelligent receipt management system that uses AI to extract data from receipt images and provides natural language querying capabilities.


## 🎯 Project Overview

**Project Raseed** is built incrementally across 5 steps:

- ✅ **Step 1**: Receipt Upload + Firebase Storage (COMPLETE)
- ✅ **Step 2**: Gemini Vision AI Integration (COMPLETE)
- 🔄 **Step 3**: Google Wallet Pass Generation (Next)
- 🔄 **Step 4**: Natural Language Query System
- 🔄 **Step 5**: Insights & Push Notifications

## 🏗️ Architecture

```
Frontend (React) ←→ Backend (FastAPI) ←→ Firebase (Storage + Firestore)
                                     ↓
                               Gemini AI APIs
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.8+ and pip
- **Firebase Project** (see setup below)
- **Google Cloud Project** with Gemini API access

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/project-raseed.git
cd project-raseed
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env with your credentials (see Firebase Setup below)

# Run backend server
python main.py
```

Backend will run on `http://localhost:8000`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env
# Edit with your API URL (default: http://localhost:8000)

# Start development server
npm start
```

Frontend will run on `http://localhost:3000`

## 🔥 Firebase Setup Guide

### Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **"Create a project"**
3. Enter project name: `project-raseed` (or your preferred name)
4. Enable Google Analytics (optional)
5. Click **"Create project"**

### Step 2: Enable Required Services

#### Enable Firestore Database
1. In Firebase Console → **Firestore Database**
2. Click **"Create database"**
3. Choose **"Start in test mode"** (we'll secure it later)
4. Select your region (choose closest to your users)
5. Click **"Done"**

#### Enable Firebase Storage
1. In Firebase Console → **Storage**
2. Click **"Get started"**
3. Review security rules → **"Next"**
4. Choose storage location → **"Done"**

### Step 3: Create Service Account

1. Go to **Project Settings** (gear icon)
2. Navigate to **"Service accounts"** tab
3. Click **"Generate new private key"**
4. Save the JSON file as `firebase-service-account.json`
5. Place this file in your `backend/` directory

### Step 4: Get Configuration Values

From the downloaded JSON file, extract these values for your `.env`:

```bash
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
```

### Step 5: Set Security Rules (Development)

#### Firestore Rules
1. Go to **Firestore Database** → **Rules**
2. Replace with:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow read/write access to all documents for development
    match /{document=**} {
      allow read, write: if true;
    }
  }
}
```

#### Storage Rules
1. Go to **Storage** → **Rules**
2. Replace with:

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // Allow read/write access to all files for development
    match /{allPaths=**} {
      allow read, write: if true;
    }
  }
}
```

**⚠️ Production Note**: These rules are for development only. See [Production Security](#production-security) section for secure rules.

## 🤖 Gemini AI Setup Guide

### Step 1: Enable Gemini API

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the API key

### Step 2: Add to Environment

Add to your `backend/.env`:

```bash
GEMINI_API_KEY=your-gemini-api-key-here
```

### Step 3: Enable Additional APIs (for Steps 3-4)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable these APIs:
   - **Vertex AI API** (for advanced AI features)
   - **Google Wallet API** (for digital passes)
   - **Cloud Translation API** (for multi-language support)

## 📁 Project Structure

```
project-raseed/
├── backend/
│   ├── app/
│   │   ├── api/routes.py           # API endpoints
│   │   ├── core/
│   │   │   ├── config.py           # Configuration
│   │   │   ├── database.py         # Firebase connection
│   │   │   └── logging.py          # Logging setup
│   │   ├── models/receipt.py       # Data models
│   │   └── services/
│   │       ├── receipt_service.py  # Receipt operations
│   │       ├── ai_service.py       # AI integration (Step 2)
│   │       ├── wallet_service.py   # Wallet integration (Step 3)
│   │       └── query_service.py    # Query system (Step 4)
│   ├── main.py                     # FastAPI app entry
│   ├── requirements.txt            # Python dependencies
│   ├── .env                        # Environment variables
│   └── firebase-service-account.json
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout/             # Header, Sidebar
│   │   │   ├── Upload/             # Upload component
│   │   │   ├── Receipt/            # Receipt cards & lists
│   │   │   └── Query/              # Query interface
│   │   ├── pages/                  # Page components
│   │   ├── services/               # API services
│   │   ├── context/                # React context
│   │   └── styles/                 # CSS styles
│   ├── package.json
│   └── .env
└── README.md
```

## 🔐 Environment Configuration

### Backend `.env` File

```bash
# Project Configuration
PROJECT_NAME="Project Raseed API"
DEBUG=true
HOST=0.0.0.0
PORT=8000

# Firebase Configuration
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com

# AI Configuration
GEMINI_API_KEY=your-gemini-api-key

# For Future Steps
OPENAI_API_KEY=your-openai-key (optional)
GOOGLE_WALLET_ISSUER_ID=your-wallet-issuer-id (Step 3)
```

### Frontend `.env` File

```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=development
```

## 🧪 Testing Your Setup

### 1. Test Backend Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "firebase_initialized": true,
  "timestamp": "2025-07-18T10:30:00Z"
}
```

### 2. Test File Upload

```bash
curl -X POST http://localhost:8000/api/upload-receipt \
  -F "file=@test-receipt.jpg"
```

### 3. Test Frontend

1. Open `http://localhost:3000`
2. Navigate to Upload page
3. Upload a receipt image
4. Check it appears in Receipts page
5. Verify file appears in Firebase Storage console

## 🔒 Production Security

### Firestore Security Rules (Production)

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can only access their own receipts
    match /receipts/{receiptId} {
      allow read, write: if request.auth != null 
                        && request.auth.uid == resource.data.userId;
      allow create: if request.auth != null 
                   && request.auth.uid == request.resource.data.userId;
    }
    
    // Users can access their profile
    match /users/{userId} {
      allow read, write: if request.auth != null 
                        && request.auth.uid == userId;
    }
  }
}
```

### Storage Security Rules (Production)

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // Users can upload to their folder
    match /receipts/{userId}/{receiptFile} {
      allow create: if request.auth != null 
                   && request.auth.uid == userId
                   && request.resource.size < 10 * 1024 * 1024;
      allow read, delete: if request.auth != null 
                         && request.auth.uid == userId;
    }
  }
}
```

## 🚢 Deployment

### Backend Deployment Options

#### Option 1: Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

#### Option 2: Google Cloud Run
```bash
# Build and deploy
gcloud run deploy project-raseed-api \
  --source . \
  --platform managed \
  --region us-central1
```

### Frontend Deployment

#### Firebase Hosting
```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login and initialize
firebase login
firebase init hosting

# Build and deploy
npm run build
firebase deploy
```

## 🎯 Development Roadmap

### ✅ Step 1: Upload & Storage (COMPLETE)
- [x] Drag & drop file upload
- [x] Firebase Storage integration
- [x] Firestore metadata storage
- [x] Receipt listing and management
- [x] Responsive UI design

### 🔄 Step 2: AI Integration (NEXT)
- [ ] Gemini Vision API integration
- [ ] Receipt data extraction (merchant, items, totals)
- [ ] Structured data storage
- [ ] Processing status tracking

### 🔄 Step 3: Wallet Integration
- [ ] Google Wallet API setup
- [ ] Digital pass generation
- [ ] Pass customization
- [ ] QR code integration

### 🔄 Step 4: Query System
- [ ] Natural language processing
- [ ] Vertex AI Agent Builder
- [ ] Multi-language support
- [ ] Query result formatting

### 🔄 Step 5: Insights & Notifications
- [ ] Spending analysis
- [ ] Push notifications
- [ ] Dynamic pass updates
- [ ] Trend analysis

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 API Documentation

Once running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🐛 Troubleshooting

### Common Issues

#### "Firebase not initialized"
- Check your `firebase-service-account.json` file is in `backend/` directory
- Verify all Firebase environment variables are set
- Ensure Firebase project has Firestore and Storage enabled

#### "CORS errors"
- Check `ALLOWED_ORIGINS` in `backend/app/core/config.py`
- Verify frontend URL is included in CORS settings

#### "Module not found" errors
- Run `pip install -r requirements.txt` in backend
- Run `npm install` in frontend
- Check Python virtual environment is activated

#### Upload fails silently
- Check browser network tab for API errors
- Verify file size under 10MB
- Check Firebase Storage rules allow uploads

### Debug Mode

Enable debug logging in backend:
```bash
export DEBUG=true
python main.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the excellent Python framework
- [Firebase](https://firebase.google.com/) for backend infrastructure
- [Google Gemini](https://ai.google.dev/) for AI capabilities
- [React](https://reactjs.org/) for the frontend framework
- [Lucide React](https://lucide.dev/) for beautiful icons

---

**📧 Questions?** Open an issue or reach out to the development team.

**🌟 Like this project?** Give it a star on GitHub!
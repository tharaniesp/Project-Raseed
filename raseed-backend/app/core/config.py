# app/core/config.py
from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Project Info
    PROJECT_NAME: str = "Project Raseed API"
    PROJECT_DESCRIPTION: str = "AI-Powered Receipt Management System"
    VERSION: str = "1.0.0"
    
    # Server Config
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    DEBUG: bool = True
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]  # Allow all origins in development
    
    # Firebase Configuration
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_PRIVATE_KEY: str = ""
    FIREBASE_CLIENT_EMAIL: str = ""
    FIREBASE_STORAGE_BUCKET: str = ""
    FIREBASE_SERVICE_ACCOUNT_PATH: str = "firebase-service-account.json"
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "video/mp4", "video/webm", "image/jpg"
    ]
    
    # AI/ML Configuration (Step 2)
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    
    # AI Processing Settings
    AI_PROCESSING_TIMEOUT: int = 60  # seconds
    AI_MAX_RETRIES: int = 3
    
    # AI Model Configuration - Use Google Generative AI instead of Vertex AI
    USE_VERTEX_AI: bool = False  # Disabled - publisher models not accessible
    USE_GENERATIVE_AI: bool = True  # Enabled - works with API key
    GENERATIVE_AI_MODEL: str = "gemini-1.5-flash"  # Confirmed working model
    
    # Vertex AI Configuration (Fallback - currently not working for this project)
    VERTEX_AI_LOCATION: str = "us-central1"
    VERTEX_AI_MODEL: str = "gemini-1.5-flash"  # Not accessible via Vertex AI
    
    # Natural Language Query Settings
    ENABLE_MULTI_LANGUAGE: bool = True
    DEFAULT_LANGUAGE: str = "en"
    QUERY_CACHE_TIMEOUT: int = 3600  # 1 hour in seconds
    MAX_QUERY_CACHE_SIZE: int = 100
    
    # Google Wallet Configuration (Step 3)
    GOOGLE_WALLET_ISSUER_ID: str = ""
    AUTO_GENERATE_WALLET_PASS: bool = True 
    
    # Database
    FIRESTORE_COLLECTION_RECEIPTS: str = "receipts"
    FIRESTORE_COLLECTION_USERS: str = "users"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()
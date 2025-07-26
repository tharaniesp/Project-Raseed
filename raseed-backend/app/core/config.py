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
    FIREBASE_PROJECT_ID: str = "project-raseed-b380d"
    FIREBASE_PRIVATE_KEY: str = "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDPEyIDZbf13Uxd\nfftobTr37cCAlzJQV6cd1HsHMCDU4EajPJDPoyrVJ18cIOpO/y1Ku5bu4LHIGVSc\nk7whidFRFBVFp8Nzv21feFVhSHObYmcYD4ASdXm2Wgr3r+g5ivvQDyIQfzCjfoCa\n4Va5nFmxrxLkd+SStkjYgOv6WLLjbhAYjoKtHNuQBv5o4SPBpwPMWywOsjkjM6fH\ncJJG12HdH9Ha5+yDBCs2xomaaXNN3eJpasl2+2sePoVIaxx2bNZc0YsJQO9wR+5J\nQN721BuA5NYRzSsk8yhsB3XZshnQsU6S/7vj65FEOSHc81BLAWwAih6Cgmnc/koa\ntc0/UVLhAgMBAAECggEABUYLF4EkIMQf5/YiRy1X+KeICmZUsFMzz6NL4PnGw5vK\nGhRmlOPRM+WUAHet9pt8/BfKrwmkfBskCor1z2NZhAoh8A4Rli2C/oZQ+KsovDrI\nHhwKnT27aauBob+hEgfCJGZ27eq1UrFGhcXqczaXhK+icynYAFdZg9UFstCb5AWW\nRd+t29cQidsCub3Y+Ldw/ZIJkQwgmSQdJYFqQzf+vkJSCVmXjCgy8tTX8QhpcGtE\n7QSTMPnQ1egQrRD/KLYCXBVGFGBW0+Op+Aj+nRNZ4tuDts9UZ9Ta/cgw5H+MI+OC\nFtigEG4noV9LLbQqhKcg//v+nTmhkyOtko/EiZsWyQKBgQDxGbDJnTGv+1qjn5Je\nQPYIvY2EhX/dnyryWzjg8atruBLvbYuKbEOqCg0/+gB9YyPfZDCkUFQmfHm5ZGNs\ntLt3Dom8sSUeEv3mYvP6y7iVx+A+c1cQcPon+Dot7ckT0Y0NDhI1OqCVVPSKULLD\nh6+P5L+/GMJmbj5yY/uBpdkKmQKBgQDb3ySGHg+HCK36b9l8LtS5o4prnv+NmS5Q\nNgUMahM9sKzZEgJH6XQwAXUWPLppEySCA7mjDNiLlNrtoJRhIs1fa2B+ohOX6eCY\nsxH2r1Cfrrfgtod0WVKSXgg3b5qSuj6E/bb7EBoAXABfy0pJmM3dSuyX9t/dRp04\n/bxh+Wc/iQKBgQDnwY87rlv10wLkp94VthIKgtMHISCxU2//+YoqSIREDnQ9LKrm\ny30bdYAZEGLqJKN1+CP9vq21NQ/5ErOz6eMN5a6m8A1C5HSlwlbOrIdpivFWdp6p\nUkBUrXqXbaxM3bDdbLo56no0Ma7DSiEcbVBoXDWpJs6vkad7Y/p+PILueQKBgGpT\n3ejR7rZhlykOIAGy8AKaON1Utcb3NfNqPETFo2po3x3WXK4EEsEIY2QOmCMqM7SA\nMqzMEIhnwvu5dSgIWYL0fWSf4pPLcWbG6j/+hiHCr3+HJbg5XfoUaSrN2NVuJb/Q\npkWBguF7nF63A8TVlXCXxBS1OYtbk7q00f4bSzfpAoGBAJS74UiUcBq2RGLxFknJ\nxeifu5AB+zrIjomTTULkM47Z5Wfy4vuxjOBafF22esOqxe9hyPZlGmEnBTYP2gs1\nZpoOwV6PmZ1TU3R2vaFDSNpBb1T9oDc1IOdEEm6E0u0vGrP+SZPbFuuRhPbQSJms\nSgAk50QedXy8Zd7VNMYz3Ymv\n-----END PRIVATE KEY-----\n"
    FIREBASE_CLIENT_EMAIL: str = "firebase-adminsdk-fbsvc@project-raseed-b380d.iam.gserviceaccount.com"
    FIREBASE_STORAGE_BUCKET: str = "project-raseed-b380d.firebasestorage.app"
    FIREBASE_SERVICE_ACCOUNT_PATH: str = "firebase-service-account.json"
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "video/mp4", "video/webm", "image/jpg"
    ]
    
    # AI/ML Configuration (Step 2)
    GEMINI_API_KEY: str = "AIzaSyDc07PX6qoo0XpEfOE1UERcnsF0lOXL8Mk"
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
    GOOGLE_WALLET_ISSUER_ID: str = "3388000000022971806"
    AUTO_GENERATE_WALLET_PASS: bool = True 
    
    # Database
    FIRESTORE_COLLECTION_RECEIPTS: str = "receipts"
    FIRESTORE_COLLECTION_USERS: str = "users"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()
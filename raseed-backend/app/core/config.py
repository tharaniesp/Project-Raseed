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
    PORT: int = 8000
    DEBUG: bool = True
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://localhost:3000"
    ]
    
    # Firebase Configuration
    FIREBASE_PROJECT_ID: str = "project-raseed-8e636"
    FIREBASE_PRIVATE_KEY: str = "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC34qATdTm2UCF3\nnphExBWpo/3y8jorY6nfMnbVrpgj/qImsw3O3j01ax34mDrbQB/W6f3rUOUWlXsl\nUIqHSyWR160i3lY/EC6YEq9lMfTd8eWns4VXaBBhqHODBku1ZSrs2WM1Kdb8Sdkg\n3RuOVr+Hh9Cu3zg0zyFQ8c+zGDr+aBxUeocDMRsviN9jE21pbk1oX9Z6aOv0VZ+B\nP6TZrm7LViPOZDh34shV2BXZnZ8Q3uxQ4Onybfi1KMj21VdLGIRQucUjuzRp5P0V\nslq47rBYzMuPpFSl+Ez1ceNw4sEjRosaMe8TukGEOulvwCGX1tnIWpVkkJSLN5VB\nPGmdW0W3AgMBAAECggEAGPkHF6gQ6WiNKFX6hJmYqOGOSHiLBn981MS2t3hZoxx0\nCwtqxvsO7E/wJxBi1d8p3ncIC/WALIaqeGaCxF2j7DWShtdpIRwNJ+FJvqrVKsXX\nlDng1FOxUyycW2FMgNsMxFPAPGUX6aAMg9ZjZVD0ppmpm/DRYk1K+gI3sdvgOdJ7\nZHigGmVxW54Iu/1PXcCGnjZXs2S6dowJSPFuvM/0orZhAWr5Y/N7UaV0s5CKNBge\nOZwUExMAqx0lqbR3vh4v815DXxxcagqBTr64aBh1T8uuZXWbADRP9AhsdaiwcY5u\ni7upzvoxtvy2Howit5Wmp+gnNvOFHKjrVVl6fC3b2QKBgQDnv+p9NBRPormenzxb\ndO37T/pruKKB05/qyvdkd91p9nX9IcxxniSrh572cntvXXQOxF3vBHSBVAW86HEN\nQ+VFlqd6O0DOiCkmSVu88VRG/fNMPfidEcCpS9Xm5SlheR4eHeEdiFy3ZLx9CL0C\niSRJJ4gP0aghcLkClAXg2FGBywKBgQDLIIXSDmKIgHf09Gjvo5qNLCDxyZiIPBPo\n0lCo0q59jLft684MZFhv77qYDaeTk47ZKmIB+1F6lA/vi/oJFWux9s2YTt9U0FMr\nkKeFrn86eTk3CJzfLAAGwCiCGXa3pL6Vq76eth3eAA2hllbQXrcQccMVB+xjabTs\n8j1uutieRQKBgCzlKPAIXsbupzbrci3lgRTmcYTcx96OuLQrjbGQ5vvYGxNmsMxx\n7nisVUc49mCkog8aS3g6TLehJ1tpTD1dodTRUrCDOhLInfAk1fjMZ585IyDqAHet\nML2bS1znmBSh+gurjijCefOtODagsr0DBFyHo/wsiX2w8KZnNpxQS7nxAoGAUAVd\n8qSMGK5Tk4J9nHpdNmQ+DkKW/oR8a2n/MKLe7sLy6p3MrIETffV5EtG+RJsK2W6i\n8ZjqPln59Sq1s8JmjNNnpyrbPHRdb3orJLTbllOPQKj588lHsWEeFDKn3Czgj+H6\n1Fd2aLCorhGl3aySfb3zVmOqsndAOWAs52RgVekCgYEAkGrhIAT0NPOoW0hqQP35\nPSpre+4zt8gFOgqBpkvfSSwUcsbbMjtgVUTpzLgnl1DfpIYehtoFhdHB/fQx/nx/\n0fSokt7tOGpU5X34kssS07uoNz79lNUfJ8tcYdt9si+3oMcSBCGlslVdU2AelaC2\n7vr31zRUI1D7UmFErGytsKo=\n-----END PRIVATE KEY-----\n"
    FIREBASE_CLIENT_EMAIL: str = "firebase-adminsdk-fbsvc@project-raseed-8e636.iam.gserviceaccount.com"
    FIREBASE_STORAGE_BUCKET: str = "project-raseed-8e636.firebasestorage.app"
    FIREBASE_SERVICE_ACCOUNT_PATH: str = "firebase-service-account.json"
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "video/mp4", "video/webm", "image/jpg"
    ]
    
    # AI/ML Configuration - Use Google Generative AI (proven to work)
    GEMINI_API_KEY: str = "AIzaSyCem5cxDNTWmu_bmB3Z3XYnsOPy-cfzenw"
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
    GOOGLE_WALLET_ISSUER_ID: str = "3388000000022971095"
    AUTO_GENERATE_WALLET_PASS: bool = True 
    
    # Database
    FIRESTORE_COLLECTION_RECEIPTS: str = "receipts"
    FIRESTORE_COLLECTION_USERS: str = "users"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()
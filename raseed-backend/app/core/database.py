import firebase_admin
from firebase_admin import credentials, firestore, storage
import os
import logging
from typing import Optional, Any
import json

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global Firebase clients
db: Optional[firestore.Client] = None
bucket: Optional[Any] = None  # Firebase storage bucket type
firebase_initialized: bool = False

def initialize_firebase() -> bool:
    """Initialize Firebase Admin SDK"""
    global db, bucket, firebase_initialized

    if firebase_initialized:
        logger.info("Firebase already initialized")
        return True

    try:
        # Option 1: Use service account file
        if os.path.exists(settings.FIREBASE_SERVICE_ACCOUNT_PATH):
            with open(settings.FIREBASE_SERVICE_ACCOUNT_PATH, 'r') as f:
                service_account = json.load(f)

            cred = credentials.Certificate(service_account)

            # 🔧 FIX: Use .env-provided bucket if available
            storage_bucket = settings.FIREBASE_STORAGE_BUCKET or service_account.get('project_id') + ".appspot.com"

            firebase_admin.initialize_app(cred, {
                'storageBucket': storage_bucket
            })

            logger.info(f"✅ Firebase initialized using service account file")
            logger.info(f"Using storage bucket: {storage_bucket}")

        # Option 2: Use environment variables (for Docker/CI/CD)
        elif settings.FIREBASE_PROJECT_ID and settings.FIREBASE_PRIVATE_KEY:
            cred_dict = {
                "type": "service_account",
                "project_id": settings.FIREBASE_PROJECT_ID,
                "private_key": settings.FIREBASE_PRIVATE_KEY.replace('\\n', '\n'),
                "client_email": settings.FIREBASE_CLIENT_EMAIL,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }

            cred = credentials.Certificate(cred_dict)

            # 🔧 FIX: Use .env-provided bucket if available
            storage_bucket = settings.FIREBASE_STORAGE_BUCKET or f"{settings.FIREBASE_PROJECT_ID}.appspot.com"

            firebase_admin.initialize_app(cred, {
                'storageBucket': storage_bucket
            })

            logger.info(f"✅ Firebase initialized using environment variables")
            logger.info(f"Using storage bucket: {storage_bucket}")

        else:
            logger.warning("⚠️ Firebase credentials not found - running in demo mode")
            return False

        # Initialize Firebase clients
        db = firestore.client()
        bucket = storage.bucket()
        firebase_initialized = True

        return True

    except Exception as e:
        logger.error(f"❌ Firebase initialization failed: {e}")
        return False

def get_firestore_client() -> Optional[firestore.Client]:
    """Get Firestore client"""
    return db

def get_storage_bucket() -> Optional[Any]:
    """Get Storage bucket"""
    return bucket

def is_firebase_initialized() -> bool:
    """Check if Firebase is initialized"""
    return firebase_initialized

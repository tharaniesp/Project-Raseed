#!/usr/bin/env python3
"""
Script to check current configuration and verify fallback mode status
"""

import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import settings

def check_configuration():
    """Check and display current configuration"""
    print("🔍 Checking Project Raseed Configuration...")
    print("=" * 50)
    
    # Check AI Configuration
    print("🤖 AI Configuration:")
    print(f"  • GEMINI_API_KEY: {'✅ Set' if settings.GEMINI_API_KEY else '❌ Not Set'}")
    print(f"  • USE_GENERATIVE_AI: {settings.USE_GENERATIVE_AI}")
    print(f"  • GENERATIVE_AI_MODEL: {settings.GENERATIVE_AI_MODEL}")
    print(f"  • USE_VERTEX_AI: {settings.USE_VERTEX_AI}")
    print(f"  • VERTEX_AI_MODEL: {settings.VERTEX_AI_MODEL}")
    
    # Check Fallback Configuration
    print("\n🔄 Fallback Configuration:")
    print(f"  • ENABLE_AI_FALLBACK_MODE: {settings.ENABLE_AI_FALLBACK_MODE}")
    print(f"  • FORCE_FALLBACK_MODE: {settings.FORCE_FALLBACK_MODE}")
    
    # Check Firebase Configuration
    print("\n🔥 Firebase Configuration:")
    print(f"  • FIREBASE_PROJECT_ID: {'✅ Set' if settings.FIREBASE_PROJECT_ID else '❌ Not Set'}")
    print(f"  • FIREBASE_STORAGE_BUCKET: {'✅ Set' if settings.FIREBASE_STORAGE_BUCKET else '❌ Not Set'}")
    
    # Check Wallet Configuration
    print("\n💳 Wallet Configuration:")
    print(f"  • GOOGLE_WALLET_ISSUER_ID: {'✅ Set' if settings.GOOGLE_WALLET_ISSUER_ID else '❌ Not Set'}")
    print(f"  • AUTO_GENERATE_WALLET_PASS: {settings.AUTO_GENERATE_WALLET_PASS}")
    
    # Check Server Configuration
    print("\n🚀 Server Configuration:")
    print(f"  • HOST: {settings.HOST}")
    print(f"  • PORT: {settings.PORT}")
    print(f"  • DEBUG: {settings.DEBUG}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Configuration Summary:")
    
    issues = []
    
    if not settings.GEMINI_API_KEY:
        issues.append("❌ GEMINI_API_KEY not set")
    
    if settings.FORCE_FALLBACK_MODE:
        issues.append("❌ FORCE_FALLBACK_MODE is enabled - AI features disabled")
    
    if not settings.FIREBASE_PROJECT_ID:
        issues.append("❌ FIREBASE_PROJECT_ID not set")
    
    if not settings.GOOGLE_WALLET_ISSUER_ID:
        issues.append("❌ GOOGLE_WALLET_ISSUER_ID not set")
    
    if issues:
        print("⚠️ Issues Found:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("✅ Configuration looks good!")
    
    # Recommendations
    print("\n💡 Recommendations:")
    if settings.FORCE_FALLBACK_MODE:
        print("  • Set FORCE_FALLBACK_MODE = False to enable AI features")
    if not settings.GEMINI_API_KEY:
        print("  • Set GEMINI_API_KEY to enable AI processing")
    if not settings.FIREBASE_PROJECT_ID:
        print("  • Set FIREBASE_PROJECT_ID for database functionality")
    
    print("\n🔄 To apply configuration changes, restart the server:")
    print("  • Stop the current server (Ctrl+C)")
    print("  • Run: python main.py")

if __name__ == "__main__":
    check_configuration() 
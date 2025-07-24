#!/usr/bin/env python3
"""
Vertex AI Configuration Validator
Checks if Vertex AI Agent Builder is properly configured and accessible
"""

import os
import sys
import logging
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

def check_environment_variables():
    """Check required environment variables"""
    print("🔧 Checking Environment Variables...")
    
    required_vars = {
        'FIREBASE_PROJECT_ID': os.getenv('FIREBASE_PROJECT_ID'),
        'VERTEX_AI_LOCATION': os.getenv('VERTEX_AI_LOCATION', 'us-central1')
    }
    
    optional_vars = {
        'VERTEX_AI_MODEL': os.getenv('VERTEX_AI_MODEL', 'gemini-1.5-pro')
    }
    
    all_set = True
    for var, value in required_vars.items():
        status = "✅" if value else "❌"
        print(f"  {status} {var}: {value or 'NOT SET'}")
        if not value:
            all_set = False
    
    print(f"\n🔧 Optional Configuration:")
    for var, value in optional_vars.items():
        print(f"  ℹ️ {var}: {value}")
    
    return all_set

def check_packages():
    """Check if required packages are installed"""
    print("\n📦 Checking Required Packages...")
    
    packages = {
        'vertexai': 'vertexai',
        'google.cloud.aiplatform': 'google-cloud-aiplatform',
        'langdetect': 'langdetect',
        'googletrans': 'googletrans'
    }
    
    all_installed = True
    for import_name, package_name in packages.items():
        try:
            # A bit of a hack to handle the different import names
            __import__(import_name)
            print(f"  ✅ {package_name}")
        except ImportError:
            print(f"  ❌ {package_name} - Run: pip install {package_name}")
            all_installed = False
    
    return all_installed

def test_vertex_ai_connection():
    """Test Vertex AI Generative AI connection by trying multiple models."""
    print("\n🤖 Testing Vertex AI Generative AI...")
    
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
        
        project_id = os.getenv('FIREBASE_PROJECT_ID')
        location = "us-central1"
        
        print(f"  - Using Project ID: {project_id}")
        print(f"  - Using Location: {location}")

        if not project_id:
            print("  ❌ Missing FIREBASE_PROJECT_ID")
            return False
        
        vertexai.init(project=project_id, location=location)
        print(f"  ✅ Vertex AI SDK initialized successfully.")
        
        # --- Diagnostic: Try a list of standard models ---
        models_to_try = [
            "gemini-1.0-pro",
            "gemini-1.0-pro-vision", # Often available
            "gemini-pro", # A common alias
            "gemini-1.5-flash"
        ]
        
        working_model = None
        for model_name in models_to_try:
            try:
                print(f"\n  - Attempting to access model: '{model_name}'...")
                model = GenerativeModel(model_name)
                response = model.generate_content("test") # Simple test prompt
                if response.text:
                    print(f"  ✅ SUCCESS! Your project has access to '{model_name}'.")
                    working_model = model_name
                    break # Stop on the first success
            except Exception:
                print(f"  - ❌ Model '{model_name}' not accessible.")
        
        if working_model:
            print(f"\n  RECOMMENDATION: Set this in your .env file: VERTEX_AI_MODEL={working_model}")
            return True
        else:
            print("\n  ---")
            print("  ❌ CRITICAL: No working Gemini models found in this project/region.")
            print("  💡 Please double-check your Google Cloud project setup:")
            print("     1. Ensure Billing is enabled for your project.")
            print("     2. Ensure the 'Vertex AI API' is enabled.")
            print("     3. Ensure your user has the 'Vertex AI User' IAM role.")
            return False
        
    except Exception as e:
        print(f"  ❌ A critical error occurred during Vertex AI initialization: {e}")
        return False

def test_language_detection():
    """Test language detection functionality"""
    print("\n🌐 Testing Language Detection...")
    
    try:
        from langdetect import detect
        
        test_queries = {
            "What can I cook?": "en",
            "¿Qué puedo cocinar?": "es",
            "Qu'est-ce que je peux cuisiner?": "fr"
        }
        
        for query, expected_lang in test_queries.items():
            try:
                detected = detect(query)
                status = "✅" if detected == expected_lang else "⚠️"
                print(f"  {status} '{query}' -> {detected} (expected: {expected_lang})")
            except Exception as e:
                print(f"  ❌ Error detecting language for '{query}': {e}")
                return False
        
        return True
        
    except ImportError:
        print("  ❌ langdetect not installed")
        return False

async def test_translation():
    """Test translation functionality"""
    print("\n🔄 Testing Translation...")
    
    try:
        from googletrans import Translator
        
        translator = Translator()
        
        # Test translation
        test_text = "¿Qué puedo cocinar?"
        translated = await translator.translate(test_text, src='es', dest='en')
        
        print(f"  ✅ Spanish to English: '{test_text}' -> '{translated.text}'")
        return True
        
    except ImportError:
        print("  ❌ googletrans not installed")
        return False
    except Exception as e:
        print(f"  ❌ Translation error: {e}")
        return False

async def main():
    """Main validation function"""
    print("🚀 Vertex AI Configuration Validator")
    print("=" * 50)
    
    # Run all checks
    checks = [
        ("Environment Variables", check_environment_variables),
        ("Required Packages", check_packages),
        ("Vertex AI Connection", test_vertex_ai_connection),
        ("Language Detection", test_language_detection)
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} failed with error: {e}")
            results.append((check_name, False))

    # Test translation separately with asyncio
    results.append(("Translation Service", await test_translation()))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for check_name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {check_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} checks passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 PERFECT! Vertex AI is fully configured and ready!")
        print("   Your backend should now use Vertex AI Agent Builder.")
    elif passed >= 3:
        print("🟡 MOSTLY READY! Minor issues to resolve.")
        print("   Basic functionality should work.")
    else:
        print("🔴 CONFIGURATION NEEDED! Several issues to fix.")
        print("   Check the failed items above.")
    
    print(f"\n💡 Next Steps:")
    if passed == total:
        print("   - Restart your FastAPI server")
        print("   - Test queries through the API")
        print("   - Vertex AI should now be active instead of Gemini fallback")
    else:
        print("   - Fix the failed configuration items")
        print("   - Ensure your Vertex AI Data Store exists in Google Cloud Console")
        print("   - Verify API permissions and authentication")

if __name__ == "__main__":
    asyncio.run(main()) 
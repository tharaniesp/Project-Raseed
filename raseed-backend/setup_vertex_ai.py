#!/usr/bin/env python3
"""
Setup script for Vertex AI Agent functionality
Checks dependencies and provides setup instructions
"""

import subprocess
import sys
import os
from typing import List, Tuple

def check_package_installed(package: str) -> bool:
    """Check if a Python package is installed"""
    try:
        __import__(package.replace('-', '_'))
        return True
    except ImportError:
        return False

def install_packages(packages: List[str]) -> bool:
    """Install required packages"""
    print(f"📦 Installing packages: {', '.join(packages)}")
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '--upgrade'
        ] + packages)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        return False

def check_vertex_ai_setup():
    """Check Vertex AI setup and provide instructions"""
    print("🔍 Checking Vertex AI Setup")
    print("=" * 50)
    
    # Check required packages
    required_packages = {
        'google-cloud-discoveryengine': 'google.cloud.discoveryengine',
        'google-cloud-dialogflow-cx': 'google.cloud.dialogflow_cx',
        'langdetect': 'langdetect',
        'googletrans': 'googletrans'
    }
    
    missing_packages = []
    
    print("\n📋 Package Status:")
    for package, import_name in required_packages.items():
        installed = check_package_installed(import_name)
        status = "✅" if installed else "❌"
        print(f"  {status} {package}")
        if not installed:
            missing_packages.append(package)
    
    # Check environment variables
    print("\n🔧 Environment Configuration:")
    env_vars = {
        'FIREBASE_PROJECT_ID': os.getenv('FIREBASE_PROJECT_ID'),
        'VERTEX_AI_LOCATION': os.getenv('VERTEX_AI_LOCATION', 'global'),
        'VERTEX_AI_DATA_STORE_ID': os.getenv('VERTEX_AI_DATA_STORE_ID'),
    }
    
    for var, value in env_vars.items():
        status = "✅" if value else "❌"
        print(f"  {status} {var}: {value or 'Not set'}")
    
    # Provide instructions
    print("\n🛠️ Setup Instructions:")
    
    if missing_packages:
        print(f"\n1. Install missing packages:")
        print(f"   pip install {' '.join(missing_packages)}")
        
        if input("\n📦 Install missing packages now? (y/n): ").lower() == 'y':
            if install_packages(missing_packages):
                print("✅ Packages installed successfully!")
            else:
                print("❌ Package installation failed")
                return False
    
    if not env_vars['FIREBASE_PROJECT_ID']:
        print(f"\n2. Set FIREBASE_PROJECT_ID in your .env file:")
        print(f"   FIREBASE_PROJECT_ID=your-project-id")
    
    if not env_vars['VERTEX_AI_DATA_STORE_ID']:
        print(f"\n3. Create Vertex AI Data Store:")
        print(f"   - Go to Google Cloud Console")
        print(f"   - Navigate to Vertex AI > Agent Builder")
        print(f"   - Create a new Data Store")
        print(f"   - Add VERTEX_AI_DATA_STORE_ID=your-datastore-id to .env")
    
    print(f"\n4. Enable required APIs in Google Cloud Console:")
    print(f"   - Vertex AI API")
    print(f"   - Discovery Engine API")
    print(f"   - Dialogflow CX API")
    
    return len(missing_packages) == 0

def test_vertex_ai_connection():
    """Test if Vertex AI can be initialized"""
    print("\n🧪 Testing Vertex AI Connection...")
    
    try:
        from app.services.vertex_ai_agent_service import vertex_ai_agent_service
        
        if vertex_ai_agent_service is None:
            print("❌ Vertex AI service failed to initialize")
            return False
        
        is_available = vertex_ai_agent_service.is_available()
        
        if is_available:
            print("✅ Vertex AI service is available and ready!")
            return True
        else:
            print("⚠️ Vertex AI service initialized but not available")
            print("   This might be normal if packages were just installed")
            print("   Try restarting your FastAPI server")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Vertex AI: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Vertex AI Agent Setup")
    print("=" * 50)
    
    # Check current working directory
    if not os.path.exists('app'):
        print("❌ Please run this script from the raseed-backend directory")
        return
    
    # Check setup
    packages_ok = check_vertex_ai_setup()
    
    if packages_ok:
        # Test connection
        connection_ok = test_vertex_ai_connection()
        
        if connection_ok:
            print("\n🎉 Setup Complete!")
            print("   Vertex AI Agent is ready to use")
            print("   Restart your FastAPI server to see changes")
        else:
            print("\n⚠️ Setup Partially Complete")
            print("   Packages installed but service not fully configured")
            print("   Check Google Cloud Console setup")
    else:
        print("\n❌ Setup Incomplete")
        print("   Install missing packages and configure environment")
    
    print("\n📖 For detailed setup instructions, see:")
    print("   VERTEX_AI_QUERY_FEATURE.md")

if __name__ == "__main__":
    main() 
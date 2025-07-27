#!/usr/bin/env python3
"""
Script to restart the server and apply configuration changes
"""

import os
import sys
import subprocess
import time
import signal

def restart_server():
    """Restart the FastAPI server"""
    print("🔄 Restarting Project Raseed server...")
    
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if main.py exists
    main_py = os.path.join(current_dir, "main.py")
    if not os.path.exists(main_py):
        print("❌ main.py not found!")
        return False
    
    # Kill any existing server process
    try:
        # Find and kill existing Python processes running main.py
        result = subprocess.run(
            ["pkill", "-f", "python.*main.py"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ Killed existing server process")
        else:
            print("ℹ️ No existing server process found")
    except Exception as e:
        print(f"⚠️ Could not kill existing process: {e}")
    
    # Wait a moment for the process to fully terminate
    time.sleep(2)
    
    # Start the server
    try:
        print("🚀 Starting server with updated configuration...")
        
        # Change to the backend directory
        os.chdir(current_dir)
        
        # Start the server in the background
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment for the server to start
        time.sleep(3)
        
        # Check if the process is still running
        if process.poll() is None:
            print("✅ Server started successfully!")
            print(f"📊 Process ID: {process.pid}")
            print("🌐 Server should be available at: http://localhost:8080")
            print("📖 API docs at: http://localhost:8080/docs")
            return True
        else:
            # Get the error output
            stdout, stderr = process.communicate()
            print("❌ Server failed to start!")
            print(f"Error: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False

def check_server_status():
    """Check if the server is running and responding"""
    import requests
    
    try:
        response = requests.get("http://localhost:8080/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and responding!")
            return True
        else:
            print(f"❌ Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Server not responding: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Project Raseed Server Restart")
    print("=" * 40)
    
    # First check current configuration
    print("🔍 Checking current configuration...")
    subprocess.run([sys.executable, "check_config.py"])
    
    print("\n" + "=" * 40)
    
    # Restart the server
    if restart_server():
        print("\n⏳ Waiting for server to fully start...")
        time.sleep(5)
        
        # Check server status
        if check_server_status():
            print("\n🎉 Server restarted successfully!")
            print("💡 Configuration changes have been applied.")
            print("🔗 You can now test the AI features.")
        else:
            print("\n⚠️ Server may not be fully started yet.")
            print("💡 Try accessing http://localhost:8080/health in a few seconds.")
    else:
        print("\n❌ Failed to restart server.")
        print("💡 Check the error messages above and try again.") 
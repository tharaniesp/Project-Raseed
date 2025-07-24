#!/usr/bin/env python3
"""
Simple test script for basic query functionality
Tests core features without requiring all optional dependencies
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🩺 Testing Health Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check passed")
            print(f"   Firebase initialized: {data.get('firebase_initialized')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_statistics():
    """Test statistics endpoint"""
    print("\n📊 Testing Statistics Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/query/statistics")
        if response.status_code == 200:
            data = response.json()
            print("✅ Statistics endpoint working")
            print(f"   Success: {data.get('success')}")
            print(f"   Vertex AI available: {data.get('vertex_ai_available')}")
            print(f"   Wallet service available: {data.get('wallet_service_available')}")
            return True
        else:
            print(f"❌ Statistics failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Statistics error: {e}")
        return False

def test_basic_query():
    """Test basic query functionality"""
    print("\n🔍 Testing Basic Query...")
    
    query_data = {
        "query": "What can I cook with chicken?",
        "user_id": "test_user"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/query",
            json=query_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Basic query working")
            print(f"   Query type: {data.get('query_type')}")
            print(f"   Language: {data.get('detected_language')}")
            print(f"   Answer length: {len(data.get('answer', ''))}")
            print(f"   Actionable items: {len(data.get('actionable_items', []))}")
            return True
        else:
            print(f"❌ Query failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Query error: {e}")
        return False

def test_shopping_list():
    """Test shopping list generation"""
    print("\n🛒 Testing Shopping List Generation...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/query/shopping-list",
            json={
                "query": "What do I need to buy for pasta?",
                "user_id": "test_user"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Shopping list generation working")
            print(f"   Title: {data.get('title')}")
            print(f"   Items: {len(data.get('items', []))}")
            return True
        else:
            print(f"❌ Shopping list failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Shopping list error: {e}")
        return False

def main():
    """Run all basic tests"""
    print("🚀 Starting Basic Query Feature Tests")
    print(f"⏰ Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Testing against: {BASE_URL}")
    
    tests = [
        ("Health Check", test_health),
        ("Statistics", test_statistics),
        ("Basic Query", test_basic_query),
        ("Shopping List", test_shopping_list)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 Test Summary")
    print(f"{'='*50}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All basic tests passed! Core functionality is working.")
    elif passed > 0:
        print("⚠️ Some tests passed. Core system is working but some features need attention.")
    else:
        print("❌ All tests failed. Please check server configuration and logs.")
    
    print(f"⏰ Test completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 
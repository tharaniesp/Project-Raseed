#!/usr/bin/env python3
"""
Test script for Vertex AI Local Language Query Feature
Demonstrates various query types and wallet pass generation
"""

import asyncio
import json
import requests
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api"

class QueryTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        
    def print_section(self, title: str):
        """Print a formatted section header"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    
    def print_response(self, response: Dict[Any, Any], title: str = "Response"):
        """Pretty print a JSON response"""
        print(f"\n{title}:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
    
    def test_health_check(self):
        """Test if the API is healthy"""
        self.print_section("Health Check")
        
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            
            data = response.json()
            self.print_response(data, "Health Status")
            
            if data.get("firebase_initialized"):
                print("✅ Firebase initialized successfully")
            else:
                print("❌ Firebase not initialized")
                
            return True
            
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    def test_query_statistics(self):
        """Test query statistics endpoint"""
        self.print_section("Query Statistics")
        
        try:
            response = self.session.get(f"{self.base_url}/query/statistics")
            response.raise_for_status()
            
            data = response.json()
            self.print_response(data, "Statistics")
            
            if data.get("vertex_ai_available"):
                print("✅ Vertex AI available")
            else:
                print("⚠️ Vertex AI not available (will use fallback)")
                
            if data.get("wallet_service_available"):
                print("✅ Wallet service available")
            else:
                print("⚠️ Wallet service not available")
                
            return True
            
        except Exception as e:
            print(f"❌ Statistics check failed: {e}")
            return False
    
    def test_cooking_query(self):
        """Test cooking suggestions query"""
        self.print_section("Cooking Suggestions Query")
        
        query_data = {
            "query": "What can I cook with the food I bought from the last two weeks?",
            "user_id": "test_user_123"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/query",
                json=query_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            data = response.json()
            self.print_response(data, "Cooking Query Response")
            
            print(f"📊 Query Type: {data.get('query_type')}")
            print(f"🌐 Detected Language: {data.get('detected_language')}")
            print(f"📈 Confidence: {data.get('confidence')}")
            print(f"🎯 Actionable Items: {len(data.get('actionable_items', []))}")
            print(f"💳 Can Create Wallet Pass: {data.get('can_create_wallet_pass')}")
            
            return data
            
        except Exception as e:
            print(f"❌ Cooking query failed: {e}")
            return None
    
    def test_shopping_list_query(self):
        """Test shopping list generation query"""
        self.print_section("Shopping List Query")
        
        query_data = {
            "query": "I need to buy ingredients to make spaghetti carbonara",
            "user_id": "test_user_123"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/query",
                json=query_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            data = response.json()
            self.print_response(data, "Shopping List Query Response")
            
            print(f"📊 Query Type: {data.get('query_type')}")
            print(f"🛒 Actionable Items: {len(data.get('actionable_items', []))}")
            
            # Show actionable items
            if data.get('actionable_items'):
                print("\n🎯 Shopping Items:")
                for i, item in enumerate(data['actionable_items'], 1):
                    print(f"  {i}. {item.get('quantity', '1')}x {item.get('name')} ({item.get('category', 'other')})")
            
            return data
            
        except Exception as e:
            print(f"❌ Shopping list query failed: {e}")
            return None
    
    def test_multilingual_query(self):
        """Test multi-language query"""
        self.print_section("Multi-Language Query")
        
        # Test Spanish query
        query_data = {
            "query": "¿Qué puedo cocinar con pollo y arroz?",
            "language": "es",
            "user_id": "test_user_123"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/query",
                json=query_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            data = response.json()
            self.print_response(data, "Spanish Query Response")
            
            print(f"🌐 Original Language: es")
            print(f"🌐 Detected Language: {data.get('detected_language')}")
            print(f"📊 Query Type: {data.get('query_type')}")
            
            return data
            
        except Exception as e:
            print(f"❌ Multi-language query failed: {e}")
            return None
    
    def test_inventory_check(self):
        """Test inventory check query"""
        self.print_section("Inventory Check Query")
        
        query_data = {
            "query": "Do I have enough laundry detergent for my weekly laundry?",
            "user_id": "test_user_123"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/query",
                json=query_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            data = response.json()
            self.print_response(data, "Inventory Check Response")
            
            print(f"📊 Query Type: {data.get('query_type')}")
            print(f"📈 Confidence: {data.get('confidence')}")
            
            return data
            
        except Exception as e:
            print(f"❌ Inventory check failed: {e}")
            return None
    
    def test_wallet_pass_creation(self, query_response: Dict[str, Any]):
        """Test wallet pass creation from a query response"""
        self.print_section("Google Wallet Pass Creation")
        
        # Extract query ID from suggested actions
        query_id = None
        if query_response and query_response.get('suggested_actions'):
            for action in query_response['suggested_actions']:
                if 'Query ID:' in action:
                    query_id = action.split('Query ID: ')[1].rstrip(')')
                    break
        
        if not query_id:
            print("❌ No query ID found in previous response")
            return None
        
        wallet_data = {
            "query_id": query_id,
            "pass_title": "Test Shopping List"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/query/create-wallet-pass",
                json=wallet_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            data = response.json()
            self.print_response(data, "Wallet Pass Creation Response")
            
            if data.get('success'):
                print("✅ Wallet pass created successfully!")
                print(f"🎫 Object ID: {data.get('wallet_object_id')}")
                print(f"🔗 Save URL: {data.get('save_url')}")
                print(f"📦 Items Count: {data.get('items_count')}")
            else:
                print(f"❌ Wallet pass creation failed: {data.get('error')}")
            
            return data
            
        except Exception as e:
            print(f"❌ Wallet pass creation failed: {e}")
            return None
    
    def test_shopping_list_generation(self):
        """Test detailed shopping list generation"""
        self.print_section("Detailed Shopping List Generation")
        
        try:
            response = self.session.post(
                f"{self.base_url}/query/shopping-list",
                data={
                    "query": "What ingredients do I need to buy to make chicken curry?",
                    "user_id": "test_user_123"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            
            data = response.json()
            self.print_response(data, "Shopping List Generation Response")
            
            print(f"📝 Title: {data.get('title')}")
            print(f"📦 Items Count: {len(data.get('items', []))}")
            print(f"💰 Estimated Total: ${data.get('total_estimated_cost', 0):.2f}")
            print(f"🏪 Suggested Stores: {', '.join(data.get('suggested_stores', []))}")
            
            return data
            
        except Exception as e:
            print(f"❌ Shopping list generation failed: {e}")
            return None
    
    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🚀 Starting Comprehensive Vertex AI Query Tests")
        print(f"⏰ Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Health checks
        if not self.test_health_check():
            print("❌ Health check failed, aborting tests")
            return
        
        if not self.test_query_statistics():
            print("❌ Statistics check failed, aborting tests")
            return
        
        # Query tests
        cooking_response = self.test_cooking_query()
        shopping_response = self.test_shopping_list_query()
        multilingual_response = self.test_multilingual_query()
        inventory_response = self.test_inventory_check()
        
        # Wallet pass test (use shopping response if available)
        wallet_response = None
        if shopping_response and shopping_response.get('can_create_wallet_pass'):
            wallet_response = self.test_wallet_pass_creation(shopping_response)
        
        # Shopping list generation test
        detailed_shopping = self.test_shopping_list_generation()
        
        # Summary
        self.print_section("Test Summary")
        tests = [
            ("Health Check", True),
            ("Statistics", True),
            ("Cooking Query", cooking_response is not None),
            ("Shopping Query", shopping_response is not None),
            ("Multi-language Query", multilingual_response is not None),
            ("Inventory Check", inventory_response is not None),
            ("Wallet Pass Creation", wallet_response is not None and wallet_response.get('success')),
            ("Shopping List Generation", detailed_shopping is not None)
        ]
        
        passed = sum(1 for _, success in tests if success)
        total = len(tests)
        
        print(f"\n📊 Test Results: {passed}/{total} passed")
        for test_name, success in tests:
            status = "✅" if success else "❌"
            print(f"  {status} {test_name}")
        
        print(f"\n⏰ Test completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if passed == total:
            print("🎉 All tests passed! Vertex AI Query feature is working correctly.")
        else:
            print("⚠️ Some tests failed. Check configuration and logs for details.")

def main():
    """Main test function"""
    tester = QueryTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main() 
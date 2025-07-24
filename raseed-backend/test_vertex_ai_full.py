#!/usr/bin/env python3
"""
Comprehensive Vertex AI and Multi-Language Query Test
Tests the complete functionality with real Vertex AI integration
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class VertexAITester:
    def __init__(self):
        self.session = requests.Session()
        self.query_ids = []  # Store query IDs for wallet pass testing
    
    def print_section(self, title: str):
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    
    def print_response(self, response: Dict[Any, Any], title: str = "Response"):
        print(f"\n{title}:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
    
    def test_vertex_ai_status(self):
        """Test if Vertex AI is properly configured"""
        self.print_section("Vertex AI Configuration Status")
        
        try:
            response = self.session.get(f"{BASE_URL}/api/query/statistics")
            response.raise_for_status()
            
            data = response.json()
            self.print_response(data, "Configuration Status")
            
            vertex_ai_available = data.get('vertex_ai_available', False)
            wallet_available = data.get('wallet_service_available', False)
            
            print(f"\n📊 Status Summary:")
            print(f"   ✅ Vertex AI Available: {vertex_ai_available}")
            print(f"   ✅ Wallet Service Available: {wallet_available}")
            print(f"   📈 Cache Utilization: {data.get('statistics', {}).get('cache_utilization', '0%')}")
            
            if not vertex_ai_available:
                print(f"\n⚠️ VERTEX AI NOT AVAILABLE!")
                print(f"   - Check VERTEX_AI_DATA_STORE_ID in .env")
                print(f"   - Verify Google Cloud APIs are enabled")
                print(f"   - Restart server after configuration changes")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Status check failed: {e}")
            return False
    
    def test_multi_language_queries(self):
        """Test queries in multiple languages"""
        self.print_section("Multi-Language Query Testing")
        
        test_queries = [
            {
                "query": "What can I cook with chicken and rice?",
                "language": "en",
                "expected_type": "cooking_suggestions"
            },
            {
                "query": "¿Qué ingredientes necesito para hacer paella?", 
                "language": "es",
                "expected_type": "shopping_list"
            },
            {
                "query": "Qu'est-ce que je peux cuisiner avec du poulet?",
                "language": "fr", 
                "expected_type": "cooking_suggestions"
            },
            {
                "query": "我需要买什么食材来做炒饭?",
                "language": "zh",
                "expected_type": "shopping_list"
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n🌐 Test {i}: {test_case['language'].upper()} Query")
            print(f"   Query: {test_case['query']}")
            
            try:
                response = self.session.post(
                    f"{BASE_URL}/api/query",
                    json={
                        "query": test_case["query"],
                        "language": test_case["language"],
                        "user_id": f"test_user_{test_case['language']}"
                    },
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Check results
                detected_lang = data.get('detected_language')
                query_type = data.get('query_type')
                actionable_items = len(data.get('actionable_items', []))
                can_create_pass = data.get('can_create_wallet_pass', False)
                
                print(f"   ✅ Response received")
                print(f"   🌐 Detected Language: {detected_lang}")
                print(f"   📊 Query Type: {query_type}")
                print(f"   🛒 Actionable Items: {actionable_items}")
                print(f"   💳 Can Create Wallet Pass: {can_create_pass}")
                
                # Store query ID if wallet pass can be created
                if can_create_pass and actionable_items > 0:
                    # Extract query ID from suggested actions
                    for action in data.get('suggested_actions', []):
                        if 'Query ID:' in action:
                            query_id = action.split('Query ID: ')[1].rstrip(')')
                            self.query_ids.append({
                                'id': query_id,
                                'language': test_case['language'],
                                'items': actionable_items
                            })
                            print(f"   🆔 Query ID stored: {query_id}")
                            break
                
                results.append({
                    'language': test_case['language'],
                    'success': True,
                    'detected_language': detected_lang,
                    'query_type': query_type,
                    'actionable_items': actionable_items
                })
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                results.append({
                    'language': test_case['language'],
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def test_shopping_list_extraction(self):
        """Test specific shopping list queries"""
        self.print_section("Shopping List Extraction Testing")
        
        shopping_queries = [
            "I need to buy ingredients for spaghetti carbonara",
            "What do I need to make chicken curry?",
            "Create a shopping list for making tacos",
            "¿Qué necesito comprar para hacer gazpacho?"
        ]
        
        extracted_lists = []
        
        for i, query in enumerate(shopping_queries, 1):
            print(f"\n🛒 Shopping Test {i}: {query}")
            
            try:
                response = self.session.post(
                    f"{BASE_URL}/api/query",
                    json={
                        "query": query,
                        "user_id": f"shopping_test_{i}"
                    },
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                data = response.json()
                actionable_items = data.get('actionable_items', [])
                
                if actionable_items:
                    print(f"   ✅ Extracted {len(actionable_items)} items:")
                    for item in actionable_items:
                        print(f"      - {item.get('quantity', '1')}x {item.get('name')} ({item.get('category', 'other')})")
                    
                    extracted_lists.append({
                        'query': query,
                        'items': actionable_items,
                        'count': len(actionable_items)
                    })
                else:
                    print(f"   ⚠️ No actionable items extracted")
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
        
        return extracted_lists
    
    def test_wallet_pass_creation(self):
        """Test Google Wallet pass creation"""
        self.print_section("Google Wallet Pass Creation")
        
        if not self.query_ids:
            print("⚠️ No query IDs available for wallet pass testing")
            print("   Run shopping list tests first to generate actionable queries")
            return []
        
        created_passes = []
        
        for i, query_info in enumerate(self.query_ids, 1):
            print(f"\n🎫 Wallet Pass Test {i}: {query_info['language']} query")
            print(f"   Query ID: {query_info['id']}")
            print(f"   Items: {query_info['items']}")
            
            try:
                response = self.session.post(
                    f"{BASE_URL}/api/query/create-wallet-pass",
                    json={
                        "query_id": query_info['id'],
                        "pass_title": f"Shopping List ({query_info['language']})"
                    },
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('success'):
                    print(f"   ✅ Wallet pass created successfully!")
                    print(f"   🎫 Object ID: {data.get('wallet_object_id')}")
                    print(f"   🔗 Save URL: {data.get('save_url')}")
                    print(f"   📦 Items Count: {data.get('items_count')}")
                    
                    created_passes.append({
                        'language': query_info['language'],
                        'object_id': data.get('wallet_object_id'),
                        'save_url': data.get('save_url'),
                        'items_count': data.get('items_count')
                    })
                else:
                    print(f"   ❌ Wallet pass creation failed: {data.get('error')}")
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
        
        return created_passes
    
    def test_vertex_ai_vs_fallback(self):
        """Compare Vertex AI vs Gemini fallback responses"""
        self.print_section("Vertex AI vs Fallback Comparison")
        
        test_query = "What can I cook with the ingredients I bought this week?"
        
        print(f"🔍 Test Query: {test_query}")
        
        try:
            response = self.session.post(
                f"{BASE_URL}/api/query",
                json={
                    "query": test_query,
                    "user_id": "comparison_test"
                },
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            data = response.json()
            
            print(f"\n📊 Response Analysis:")
            print(f"   Query Type: {data.get('query_type')}")
            print(f"   Confidence: {data.get('confidence')}")
            print(f"   Answer Length: {len(data.get('answer', ''))} characters")
            print(f"   Sources: {data.get('sources', [])}")
            print(f"   Actionable Items: {len(data.get('actionable_items', []))}")
            
            # Check if using Vertex AI or fallback
            answer = data.get('answer', '')
            if 'Based on your recent purchases' in answer:
                print(f"   🎯 Using: Advanced AI (likely Vertex AI)")
            else:
                print(f"   🔄 Using: Fallback (Gemini)")
            
            return True
            
        except Exception as e:
            print(f"❌ Comparison test failed: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run all comprehensive tests"""
        print("🚀 Comprehensive Vertex AI & Multi-Language Test Suite")
        print(f"⏰ Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test results tracking
        test_results = {
            'vertex_ai_status': False,
            'multi_language': [],
            'shopping_extraction': [],
            'wallet_passes': [],
            'comparison': False
        }
        
        # Run tests in sequence
        print("\n🔍 Phase 1: Configuration Check")
        test_results['vertex_ai_status'] = self.test_vertex_ai_status()
        
        if not test_results['vertex_ai_status']:
            print("\n❌ Vertex AI not properly configured. Some tests may fail.")
        
        print("\n🌐 Phase 2: Multi-Language Testing")
        test_results['multi_language'] = self.test_multi_language_queries()
        
        print("\n🛒 Phase 3: Shopping List Extraction")
        test_results['shopping_extraction'] = self.test_shopping_list_extraction()
        
        print("\n🎫 Phase 4: Wallet Pass Creation")
        test_results['wallet_passes'] = self.test_wallet_pass_creation()
        
        print("\n🔄 Phase 5: AI Comparison")
        test_results['comparison'] = self.test_vertex_ai_vs_fallback()
        
        # Final Summary
        self.print_section("COMPREHENSIVE TEST SUMMARY")
        
        # Calculate success rates
        lang_success = len([r for r in test_results['multi_language'] if r['success']])
        lang_total = len(test_results['multi_language'])
        
        shopping_success = len(test_results['shopping_extraction'])
        
        wallet_success = len(test_results['wallet_passes'])
        
        print(f"\n📊 Test Results:")
        print(f"   🔧 Vertex AI Configuration: {'✅' if test_results['vertex_ai_status'] else '❌'}")
        print(f"   🌐 Multi-Language Queries: {lang_success}/{lang_total} passed")
        print(f"   🛒 Shopping List Extraction: {shopping_success} successful")
        print(f"   🎫 Wallet Pass Creation: {wallet_success} created")
        print(f"   🔄 AI Response Quality: {'✅' if test_results['comparison'] else '❌'}")
        
        # Overall assessment
        total_tests = 5
        passed_tests = sum([
            test_results['vertex_ai_status'],
            lang_success == lang_total,
            shopping_success > 0,
            wallet_success > 0,
            test_results['comparison']
        ])
        
        print(f"\n🎯 Overall Score: {passed_tests}/{total_tests} ({(passed_tests/total_tests)*100:.1f}%)")
        
        if passed_tests == total_tests:
            print("🎉 PERFECT! All Vertex AI features working correctly!")
        elif passed_tests >= 3:
            print("🟡 GOOD! Most features working, minor issues to address")
        else:
            print("🔴 NEEDS WORK! Several issues need to be resolved")
        
        print(f"\n⏰ Completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return test_results

def main():
    tester = VertexAITester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main() 
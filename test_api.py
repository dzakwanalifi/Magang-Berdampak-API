#!/usr/bin/env python3
"""
Test script for Magang Berdampak API
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "your-secret-api-key-here"  # Change this to your actual API key

def print_response(response: requests.Response, title: str = "Response"):
    """Pretty print API response"""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    print(f"Status Code: {response.status_code}")
    print(f"URL: {response.url}")
    
    try:
        data = response.json()
        print(f"Response JSON:\n{json.dumps(data, indent=2, ensure_ascii=False)}")
    except:
        print(f"Response Text: {response.text}")

def test_health_check():
    """Test health check endpoint"""
    print("\n🩺 Testing Health Check...")
    response = requests.get(f"{BASE_URL}/health")
    print_response(response, "Health Check")
    return response.status_code == 200

def test_root_endpoint():
    """Test root endpoint"""
    print("\n🏠 Testing Root Endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print_response(response, "Root Endpoint")
    return response.status_code == 200

def test_stats_endpoint():
    """Test stats endpoint"""
    print("\n📊 Testing Stats Endpoint...")
    response = requests.get(f"{BASE_URL}/api/v1/stats")
    print_response(response, "Stats Endpoint")
    return response.status_code == 200

def test_lowongan_list():
    """Test lowongan list endpoint with various parameters"""
    print("\n📋 Testing Lowongan List...")
    
    # Test 1: Basic list
    print("\n--- Test 1: Basic list (limit 5) ---")
    response = requests.get(f"{BASE_URL}/api/v1/lowongan?limit=5")
    print_response(response, "Basic Lowongan List")
    
    # Test 2: Search query
    print("\n--- Test 2: Search with query 'developer' ---")
    response = requests.get(f"{BASE_URL}/api/v1/lowongan?q=developer&limit=3")
    print_response(response, "Search Developer")
    
    # Test 3: Filter by location
    print("\n--- Test 3: Filter by location 'Jakarta' ---")
    response = requests.get(f"{BASE_URL}/api/v1/lowongan?lokasi=Jakarta&limit=3")
    print_response(response, "Filter Jakarta")
    
    # Test 4: Pagination
    print("\n--- Test 4: Pagination (offset 10) ---")
    response = requests.get(f"{BASE_URL}/api/v1/lowongan?limit=5&offset=10")
    print_response(response, "Pagination Test")
    
    return all(r.status_code == 200 for r in [response])

def test_lowongan_detail():
    """Test lowongan detail endpoint"""
    print("\n🔍 Testing Lowongan Detail...")
    
    # First get a list to find an ID
    list_response = requests.get(f"{BASE_URL}/api/v1/lowongan?limit=1")
    if list_response.status_code == 200:
        data = list_response.json()
        if data.get('data') and len(data['data']) > 0:
            lowongan_id = data['data'][0]['id_lowongan']
            print(f"Testing with ID: {lowongan_id}")
            
            response = requests.get(f"{BASE_URL}/api/v1/lowongan/{lowongan_id}")
            print_response(response, f"Lowongan Detail (ID: {lowongan_id})")
            return response.status_code == 200
        else:
            print("❌ No lowongan data available for detail test")
            return False
    else:
        print("❌ Failed to get lowongan list for detail test")
        return False

def test_categories_endpoint():
    """Test categories endpoint"""
    print("\n📝 Testing Categories Endpoint...")
    response = requests.get(f"{BASE_URL}/api/v1/categories")
    print_response(response, "Categories")
    return response.status_code == 200

def test_mitras_endpoint():
    """Test mitras endpoint"""
    print("\n🏢 Testing Mitras Endpoint...")
    response = requests.get(f"{BASE_URL}/api/v1/mitras")
    print_response(response, "Mitras")
    return response.status_code == 200

def test_protected_endpoint():
    """Test protected trigger-scrape endpoint"""
    print("\n🔐 Testing Protected Endpoint...")
    
    # Test without API key (should fail)
    print("\n--- Test 1: Without API key (should fail) ---")
    response = requests.post(f"{BASE_URL}/api/v1/trigger-scrape")
    print_response(response, "Trigger Scrape (No API Key)")
    
    # Test with wrong API key (should fail)
    print("\n--- Test 2: With wrong API key (should fail) ---")
    headers = {"X-API-Key": "wrong-key"}
    response = requests.post(f"{BASE_URL}/api/v1/trigger-scrape", headers=headers)
    print_response(response, "Trigger Scrape (Wrong API Key)")
    
    # Test with correct API key (should succeed)
    print("\n--- Test 3: With correct API key (should succeed) ---")
    headers = {"X-API-Key": API_KEY}
    response = requests.post(f"{BASE_URL}/api/v1/trigger-scrape", headers=headers)
    print_response(response, "Trigger Scrape (Correct API Key)")
    
    return True  # We expect some to fail, some to succeed

def test_error_cases():
    """Test error cases"""
    print("\n❌ Testing Error Cases...")
    
    # Test 1: Non-existent lowongan ID
    print("\n--- Test 1: Non-existent lowongan ID ---")
    response = requests.get(f"{BASE_URL}/api/v1/lowongan/999999")
    print_response(response, "Non-existent Lowongan")
    
    # Test 2: Invalid query parameters
    print("\n--- Test 2: Invalid limit parameter ---")
    response = requests.get(f"{BASE_URL}/api/v1/lowongan?limit=1000")  # Over max
    print_response(response, "Invalid Limit")
    
    # Test 3: Non-existent endpoint
    print("\n--- Test 3: Non-existent endpoint ---")
    response = requests.get(f"{BASE_URL}/api/v1/nonexistent")
    print_response(response, "Non-existent Endpoint")
    
    return True

def test_performance():
    """Basic performance test"""
    print("\n⚡ Testing Performance...")
    
    start_time = time.time()
    response = requests.get(f"{BASE_URL}/api/v1/lowongan?limit=50")
    end_time = time.time()
    
    duration = end_time - start_time
    print(f"Response time for 50 lowongan: {duration:.2f} seconds")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total records in DB: {data.get('total_in_db', 'N/A')}")
        print(f"Records returned: {data.get('count', 'N/A')}")
    
    return response.status_code == 200 and duration < 10.0  # Should be under 10 seconds

def main():
    """Run all tests"""
    print("🚀 Starting Magang Berdampak API Tests")
    print(f"Testing API at: {BASE_URL}")
    
    tests = [
        ("Health Check", test_health_check),
        ("Root Endpoint", test_root_endpoint),
        ("Stats Endpoint", test_stats_endpoint),
        ("Lowongan List", test_lowongan_list),
        ("Lowongan Detail", test_lowongan_detail),
        ("Categories", test_categories_endpoint),
        ("Mitras", test_mitras_endpoint),
        ("Protected Endpoint", test_protected_endpoint),
        ("Error Cases", test_error_cases),
        ("Performance", test_performance),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            print(f"Running: {test_name}")
            print(f"{'='*60}")
            
            result = test_func()
            results.append((test_name, result))
            
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"\n{status}: {test_name}")
            
        except Exception as e:
            print(f"\n💥 ERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {total - passed} tests failed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 
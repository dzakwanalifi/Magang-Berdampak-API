#!/usr/bin/env python3
"""
Test script untuk mengecek path configuration
"""

import os
import sys

def test_paths():
    """Test semua path configuration"""
    print("🔍 Testing Path Configuration...")
    
    # Current directory
    current_dir = os.getcwd()
    print(f"Current working directory: {current_dir}")
    
    # API server paths
    print("\n📂 API Server Paths:")
    api_dir = os.path.join(current_dir, 'api_new')
    api_file = os.path.join(api_dir, 'api_server.py')
    print(f"API dir exists: {os.path.exists(api_dir)} - {api_dir}")
    print(f"API file exists: {os.path.exists(api_file)} - {api_file}")
    
    # Scraper paths  
    print("\n🔧 Scraper Paths:")
    scraper_dir = os.path.join(current_dir, 'scraper_new')
    scraper_file = os.path.join(scraper_dir, 'scraper.py')
    print(f"Scraper dir exists: {os.path.exists(scraper_dir)} - {scraper_dir}")
    print(f"Scraper file exists: {os.path.exists(scraper_file)} - {scraper_file}")
    
    # Database paths
    print("\n🗄️ Database Paths:")
    db_dir = os.path.join(current_dir, 'database')
    db_file = os.path.join(db_dir, 'magang_data.db')
    cache_file = os.path.join(db_dir, 'detail_cache.json')
    print(f"Database dir exists: {os.path.exists(db_dir)} - {db_dir}")
    print(f"Database file exists: {os.path.exists(db_file)} - {db_file}")
    print(f"Cache file exists: {os.path.exists(cache_file)} - {cache_file}")
    
    # Test import paths
    print("\n🐍 Python Import Test:")
    try:
        # Add directories to path
        sys.path.insert(0, api_dir)
        sys.path.insert(0, scraper_dir)
        
        print(f"Python executable: {sys.executable}")
        print(f"Python path includes API dir: {api_dir in sys.path}")
        print(f"Python path includes Scraper dir: {scraper_dir in sys.path}")
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
    
    # Create missing directories
    print("\n📁 Creating Missing Directories:")
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        print(f"✅ Created: {db_dir}")
    else:
        print(f"✅ Already exists: {db_dir}")
    
    print("\n🎉 Path test completed!")

if __name__ == "__main__":
    test_paths() 
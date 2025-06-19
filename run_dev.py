#!/usr/bin/env python3
"""
Development runner for Magang Berdampak API
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import httpx
        import sqlite3
        print("✅ All dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def setup_directories():
    """Create necessary directories"""
    dirs = ["database", "logs"]
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
        print(f"✅ Directory created/verified: {dir_name}")

def run_initial_scrape():
    """Run scraper once to populate database"""
    if os.path.exists("database/magang_data.db"):
        print("📊 Database already exists, skipping initial scrape")
        return True
    
    print("🔄 Running initial scrape to populate database...")
    print("This may take a few minutes...")
    
    try:
        # Change to scraper directory and run
        os.chdir("scraper_new")
        result = subprocess.run([sys.executable, "scraper.py"], 
                              capture_output=True, text=True)
        os.chdir("..")
        
        if result.returncode == 0:
            print("✅ Initial scrape completed successfully")
            return True
        else:
            print(f"❌ Scraper failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running scraper: {e}")
        return False

def start_api_server():
    """Start the FastAPI development server"""
    print("🚀 Starting FastAPI development server...")
    print("API will be available at:")
    print("  - Main API: http://localhost:8000")
    print("  - Documentation: http://localhost:8000/docs")
    print("  - Alternative docs: http://localhost:8000/redoc")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        os.chdir("api_new")
        # Start uvicorn with reload
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "api_server:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--log-level", "info"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
    finally:
        os.chdir("..")

def main():
    """Main development runner"""
    print("🏗️  Magang Berdampak API - Development Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("api_new") or not os.path.exists("scraper_new"):
        print("❌ Please run this script from the magang-berdampak-api directory")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Setup directories
    setup_directories()
    
    # Ask user if they want to run initial scrape
    if not os.path.exists("database/magang_data.db"):
        response = input("\n📊 Database not found. Run initial scrape? (y/n): ").lower()
        if response in ['y', 'yes']:
            if not run_initial_scrape():
                print("❌ Failed to populate database. You can run scraper manually later.")
                print("Command: cd scraper_new && python scraper.py")
        else:
            print("⚠️  Skipping initial scrape. API will show empty data until scraper runs.")
    
    # Start API server
    print("\n" + "=" * 50)
    start_api_server()

if __name__ == "__main__":
    main() 
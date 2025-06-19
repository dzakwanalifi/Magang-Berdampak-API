import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    api_title: str = "Magang Berdampak API"
    api_description: str = "API untuk mengakses data lowongan magang dari Simbelmawa"
    api_version: str = "1.0.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Security
    api_key: str = "your-secret-api-key-here"  # Change this!
    cors_origins: list = ["*"]  # Configure properly in production
    
    # Database
    database_path: str = "../database/magang_data.db"
    cache_path: str = "../database/detail_cache.json"
    
    # Scraper Configuration
    scraper_script_path: str = "../scraper_new/scraper.py"
    base_url: str = "https://simbelmawa.kemdikbud.go.id/magang/lowongan"
    max_concurrent_requests: int = 25
    retry_count: int = 3
    retry_delay: int = 2
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Performance
    default_page_size: int = 20
    max_page_size: int = 100
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()

# Environment-specific configurations
class DevelopmentSettings(Settings):
    """Development environment settings"""
    api_host: str = "127.0.0.1"
    log_level: str = "DEBUG"

class ProductionSettings(Settings):
    """Production environment settings"""
    api_host: str = "0.0.0.0"
    log_level: str = "WARNING"
    cors_origins: list = ["https://yourdomain.com"]  # Set your actual domain

def get_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "development":
        return DevelopmentSettings()
    else:
        return Settings() 
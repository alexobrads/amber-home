"""
Configuration management for Amber-Home Data Collector Service.
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""
    
    # Required environment variables
    AMBER_API_KEY: str = os.getenv('AMBER_API_KEY', '')
    DATABASE_URL: str = os.getenv('DATABASE_URL', '')
    HISTORICAL_START_DATE: str = os.getenv('HISTORICAL_START_DATE', '')
    
    # Optional environment variables with defaults
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO').upper()
    COLLECTION_INTERVAL_MINUTES: int = int(os.getenv('COLLECTION_INTERVAL_MINUTES', '5'))
    FORCE_REINIT: bool = os.getenv('FORCE_REINIT', '').lower() == 'true'
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        missing_vars = []
        
        if not cls.AMBER_API_KEY:
            missing_vars.append('AMBER_API_KEY')
        if not cls.DATABASE_URL:
            missing_vars.append('DATABASE_URL')
        if not cls.HISTORICAL_START_DATE:
            missing_vars.append('HISTORICAL_START_DATE')
            
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
            
        # Validate date format
        try:
            cls.get_historical_start_date()
        except ValueError as e:
            raise ValueError(f"Invalid HISTORICAL_START_DATE: {e}")
    
    @classmethod
    def get_historical_start_date(cls) -> datetime:
        """Parse and return the historical start date in NEM time (AEST/AEDT)."""
        aest = ZoneInfo("Australia/Sydney")  # Handles winter/summer automatically
        try:
            # Try to parse the date string (supports formats like 2024-01-01, 2024-01-01T00:00:00, etc.)
            return datetime.fromisoformat(cls.HISTORICAL_START_DATE.replace('Z', '+00:00'))
        except ValueError:
            try:
                # Try simple date format YYYY-MM-DD and make it NEM time (AEST/AEDT)
                naive_date = datetime.strptime(cls.HISTORICAL_START_DATE, '%Y-%m-%d')
                return naive_date.replace(tzinfo=aest)
            except ValueError:
                raise ValueError(f"Invalid date format: {cls.HISTORICAL_START_DATE}. Use YYYY-MM-DD")
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment."""
        return 'railway' in cls.DATABASE_URL.lower() or 'amazonaws' in cls.DATABASE_URL.lower()
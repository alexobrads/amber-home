"""
Configuration management for Amber-Home Frontend Application.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""
    
    # Database configuration
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'postgresql://amber_user:amber_password@localhost:5432/amber_home')
    
    # Application configuration
    APP_TITLE: str = "⚡ Amber Electric Dashboard"
    PAGE_ICON: str = "⚡"
    LAYOUT: str = "wide"
    
    # Timezone configuration
    DISPLAY_TIMEZONE: str = "Australia/Sydney"
    
    # Auto-refresh configuration
    AUTO_REFRESH_SECONDS: int = int(os.getenv('AUTO_REFRESH_SECONDS', '300'))  # 5 minutes
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment."""
        return 'railway' in cls.DATABASE_URL.lower() or 'amazonaws' in cls.DATABASE_URL.lower()
"""
Business logic services for Amber-Home application.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from amber_client import AmberClient
from .database import DatabaseService
from .config import Config

logger = logging.getLogger(__name__)


class AmberService:
    """Service for Amber Electric API operations."""
    
    def __init__(self):
        self.client: Optional[AmberClient] = None
    
    def initialize(self) -> None:
        """Initialize Amber API client."""
        self.client = AmberClient(Config.AMBER_API_KEY)
        logger.info("Amber API client initialized")
    
    def get_sites(self) -> List:
        """Get all sites from Amber API."""
        if not self.client:
            raise RuntimeError("AmberService not initialized")
        
        try:
            sites = self.client.get_sites()
            logger.info(f"Retrieved {len(sites)} sites from Amber API")
            return sites
        except Exception as e:
            logger.error(f"Failed to get sites: {e}")
            raise
    
    def get_price_history(self, site_id: str, start_date: datetime, end_date: datetime) -> List:
        """Get price history for a site."""
        if not self.client:
            raise RuntimeError("AmberService not initialized")
        
        try:
            prices = self.client.get_price_history(site_id, start_date, end_date)
            logger.debug(f"Retrieved {len(prices)} price records for site {site_id}")
            return prices
        except Exception as e:
            logger.error(f"Failed to get price history for site {site_id}: {e}")
            raise
    
    def get_usage_data(self, site_id: str, start_date: datetime, end_date: datetime) -> List:
        """Get usage data for a site."""
        if not self.client:
            raise RuntimeError("AmberService not initialized")
        
        try:
            usage_data = self.client.get_usage_data(site_id, start_date, end_date)
            logger.debug(f"Retrieved {len(usage_data)} usage records for site {site_id}")
            return usage_data
        except Exception as e:
            logger.error(f"Failed to get usage data for site {site_id}: {e}")
            raise
    
    def get_current_prices_and_forecasts(self, site_id: str, next_hours: int = 24, previous_hours: int = 2) -> List:
        """
        Get current prices and forecasts for a site using the current prices endpoint.
        
        Args:
            site_id: The site ID to get prices for
            next_hours: Number of hours of forecast data to include
            previous_hours: Number of hours of recent data to include
            
        Returns:
            List of price intervals (current + forecast)
        """
        if not self.client:
            raise RuntimeError("AmberService not initialized")
        
        try:
            # Calculate number of 30-minute intervals
            next_intervals = next_hours * 2
            previous_intervals = previous_hours * 2
            
            current_prices = self.client.get_current_prices(site_id, next_hours=next_hours)
            logger.debug(f"Retrieved {len(current_prices)} current/forecast price records for site {site_id}")
            return current_prices
        except Exception as e:
            logger.error(f"Failed to get current prices for site {site_id}: {e}")
            raise
    
    def get_forecast_data(self, site_id: str, hours_ahead: int = 24) -> List:
        """Get forecast price data for a site."""
        if not self.client:
            raise RuntimeError("AmberService not initialized")
        
        try:
            forecasts = self.client.get_forecast_data(site_id, hours_ahead)
            logger.debug(f"Retrieved {len(forecasts)} forecast price records for site {site_id}")
            return forecasts
        except Exception as e:
            logger.error(f"Failed to get forecast data for site {site_id}: {e}")
            raise


class CollectionService:
    """Service for coordinating data collection operations."""
    
    def __init__(self, db_service: DatabaseService, amber_service: AmberService):
        self.db = db_service
        self.amber = amber_service
        self.sites: List = []
    
    def collect_sites(self) -> None:
        """Collect and store site information."""
        try:
            sites = self.amber.get_sites()
            self.sites = sites
            self.db.insert_sites(sites)
            logger.info(f"Collected {len(sites)} sites")
        except Exception as e:
            logger.error(f"Failed to collect sites: {e}")
            raise
    
    def collect_price_data(self, start_date: datetime, end_date: datetime) -> None:
        """Collect price data for all sites within date range."""
        if not self.sites:
            raise RuntimeError("Sites not collected yet")
        
        for site in self.sites:
            try:
                current_start = start_date
                
                while current_start < end_date:
                    current_end = min(current_start + timedelta(days=7), end_date)
                    
                    logger.info(f"Collecting prices for site {site.id} from {current_start.date()} to {current_end.date()}")
                    
                    prices = self.amber.get_price_history(site.id, current_start, current_end)
                    self.db.insert_price_data(site.id, prices)
                    
                    current_start = current_end
                    
                    # Rate limiting
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"Failed to collect price data for site {site.id}: {e}")
                continue
    
    def collect_usage_data(self, start_date: datetime, end_date: datetime) -> None:
        """Collect usage data for all sites within date range."""
        if not self.sites:
            raise RuntimeError("Sites not collected yet")
        
        for site in self.sites:
            try:
                current_start = start_date
                
                while current_start < end_date:
                    current_end = min(current_start + timedelta(days=7), end_date)
                    
                    logger.info(f"Collecting usage for site {site.id} from {current_start.date()} to {current_end.date()}")
                    
                    usage_data = self.amber.get_usage_data(site.id, current_start, current_end)
                    self.db.insert_usage_data(site.id, usage_data)
                    
                    current_start = current_end
                    
                    # Rate limiting
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"Failed to collect usage data for site {site.id}: {e}")
                continue
    
    def collect_price_data_from_date(self, start_date: datetime) -> None:
        """Collect price data from a specific date to now."""
        from zoneinfo import ZoneInfo
        # Use NEM time (AEST/AEDT) for data collection
        aest = ZoneInfo("Australia/Sydney")
        end_date = datetime.now(aest)
        
        # Ensure both dates are timezone-aware or naive
        if start_date.tzinfo is not None and end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=start_date.tzinfo)
        elif start_date.tzinfo is None and end_date.tzinfo is not None:
            start_date = start_date.replace(tzinfo=end_date.tzinfo)
        
        logger.info(f"Collecting price data from {start_date} to {end_date}")
        
        # Ensure start_date is not in the future
        if start_date > end_date:
            logger.warning(f"Price start date {start_date} is in the future, using current date")
            start_date = end_date - timedelta(days=1)
        
        self.collect_price_data(start_date, end_date)
        logger.info("Price data collection completed")
    
    def collect_usage_data_from_date(self, start_date: datetime) -> None:
        """Collect usage data from a specific date to now."""
        from datetime import timezone
        from zoneinfo import ZoneInfo
        
        # Use NEM time (AEST/AEDT) for data collection
        aest = ZoneInfo("Australia/Sydney")
        end_date = datetime.now(aest)
        
        # Ensure both dates are timezone-aware or naive
        if start_date.tzinfo is not None and end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=start_date.tzinfo)
        elif start_date.tzinfo is None and end_date.tzinfo is not None:
            start_date = start_date.replace(tzinfo=end_date.tzinfo)
        
        logger.info(f"Collecting usage data from {start_date} to {end_date}")
        
        # Ensure start_date is not in the future
        if start_date > end_date:
            logger.warning(f"Usage start date {start_date} is in the future, using current date")
            start_date = end_date - timedelta(days=1)
        
        self.collect_usage_data(start_date, end_date)
        logger.info("Usage data collection completed")
    
    def collect_historical_data(self) -> None:
        """Collect all historical data from configured start date plus initial forecasts."""
        start_date = Config.get_historical_start_date()
        logger.info(f"Collecting all historical data from {start_date}")
        
        self.collect_price_data_from_date(start_date)
        self.collect_usage_data_from_date(start_date)
        
        # Collect initial forecast data
        if Config.COLLECT_FORECASTS:
            try:
                logger.info("Collecting initial forecast data...")
                self.collect_forecast_data()
            except Exception as e:
                logger.error(f"Failed to collect initial forecast data: {e}")
                # Don't fail historical collection if forecasts fail
        else:
            logger.info("Forecast collection disabled in configuration")
        
        logger.info("Historical data collection completed (with initial forecasts)")
    
    def update_latest_data(self) -> None:
        """Update with latest data since last collection up to current time."""
        logger.info("Updating latest data...")
        
        # Get the most recent dates for each data type
        latest_price_date = self.db.get_latest_price_date()
        latest_usage_date = self.db.get_latest_usage_date()
        
        # Update price data - collect up to current time only
        from datetime import timezone
        from zoneinfo import ZoneInfo
        
        # Use NEM time (AEST/AEDT)
        aest = ZoneInfo("Australia/Sydney")
        now = datetime.now(aest)
        end_date = now  # Current time only, no future data
        
        if latest_price_date:
            price_start_date = latest_price_date + timedelta(minutes=1)
            logger.info(f"Found existing price data, collecting from {price_start_date} to {end_date}")
        else:
            price_start_date = Config.get_historical_start_date()
            logger.info(f"No existing price data found, collecting from configured start date {price_start_date} to {end_date}")
        
        self.collect_price_data(price_start_date, end_date)
        
        # Update usage data
        if latest_usage_date:
            usage_start_date = latest_usage_date + timedelta(minutes=1)
            logger.info(f"Found existing usage data, collecting from {usage_start_date}")
        else:
            usage_start_date = Config.get_historical_start_date()
            logger.info(f"No existing usage data found, collecting from configured start date {usage_start_date}")
        
        self.collect_usage_data_from_date(usage_start_date)
        
        # Always collect fresh forecast data (default enabled)
        if Config.COLLECT_FORECASTS:
            try:
                logger.info("Collecting fresh forecast data...")
                self.collect_forecast_data()
            except Exception as e:
                logger.error(f"Failed to collect forecast data: {e}")
                # Don't fail the entire update if forecast collection fails
        else:
            logger.info("Forecast collection disabled in configuration")
        
        logger.info("Latest data update completed (historical + forecasts)")
    
    def collect_forecast_data(self) -> None:
        """Collect forecast price data for all sites."""
        if not self.sites:
            raise RuntimeError("Sites not collected yet")
        
        from datetime import datetime
        from zoneinfo import ZoneInfo
        
        # Get current time for forecast generation timestamp
        aest = ZoneInfo("Australia/Sydney")
        forecast_generated_at = datetime.now(aest)
        
        # Get forecast hours configuration
        hours_ahead = Config.FORECAST_HOURS_AHEAD
        
        logger.info(f"Collecting forecast data ({hours_ahead} hours ahead) for {len(self.sites)} sites...")
        
        for site in self.sites:
            try:
                # Get forecast data for this site
                forecasts = self.amber.get_forecast_data(site.id, hours_ahead)
                
                if forecasts:
                    # Store forecast data with generation timestamp
                    self.db.insert_forecast_data(site.id, forecasts, forecast_generated_at)
                    logger.info(f"Collected {len(forecasts)} forecast records for site {site.id}")
                else:
                    logger.warning(f"No forecast data available for site {site.id}")
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to collect forecast data for site {site.id}: {e}")
                continue
        
        # Cleanup old forecasts
        retention_hours = Config.FORECAST_RETENTION_HOURS
        try:
            self.db.cleanup_old_forecasts(retention_hours)
        except Exception as e:
            logger.error(f"Failed to cleanup old forecasts: {e}")
        
        logger.info("Forecast data collection completed")
    

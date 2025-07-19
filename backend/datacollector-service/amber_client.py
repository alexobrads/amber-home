"""
Amber Electric API client wrapper for the Streamlit dashboard.
Based on patterns from Graham Lea's amberelectic-api-tools.
"""

import os
from datetime import datetime, timedelta
from typing import List, Optional
import amberelectric
from amberelectric.api import amber_api
from amberelectric.api.amber_api import Site, Usage


class AmberClient:
    """Wrapper class for Amber Electric API interactions."""
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize the Amber client.
        
        Args:
            api_token: Optional API token. If not provided, will try to get from environment.
        """
        if api_token is None:
            api_token = os.getenv('AMBER_API_KEY')
            
        if not api_token:
            raise ValueError("API token must be provided via parameter or AMBER_API_KEY environment variable")
            
        # Configure the API client for v2.0.12
        amber_configuration = amberelectric.Configuration(access_token=api_token)
        api_client = amberelectric.ApiClient(amber_configuration)
        self.client = amber_api.AmberApi(api_client)
    
    def get_sites(self) -> List[Site]:
        """Get all sites linked to the account."""
        try:
            return self.client.get_sites()
        except Exception as e:
            raise Exception(f"Failed to retrieve sites: {str(e)}")
    
    def get_current_prices(self, site_id: str, next_hours: int = 24):
        """
        Get current prices and forecasts for a site.
        
        Args:
            site_id: The site ID to get prices for
            next_hours: Number of hours of forecast data to include
            
        Returns:
            List of price intervals (current + forecast)
        """
        try:
            # Calculate number of 30-minute intervals
            next_intervals = next_hours * 2
            return self.client.get_current_prices(site_id, next=next_intervals)
        except Exception as e:
            raise Exception(f"Failed to retrieve current prices: {str(e)}")
    
    def get_usage_data(self, site_id: str, start_date: datetime, end_date: datetime):
        """
        Get usage data for a site between start and end dates.
        
        Args:
            site_id: The site ID to get usage for
            start_date: Start date for usage data (timezone-aware)
            end_date: End date for usage data (timezone-aware)
            
        Returns:
            List of usage intervals filtered to the exact time range
        """
        try:
            # API works on daily boundaries, so get all data for the date range
            start_date_api = start_date.date()
            end_date_api = end_date.date()
            all_usage = self.client.get_usage(site_id, start_date=start_date_api, end_date=end_date_api)
            
            # Filter results to exact datetime range
            filtered_usage = []
            for usage in all_usage:
                # Check if nem_time is within the requested range
                if start_date <= usage.nem_time <= end_date:
                    filtered_usage.append(usage)
            
            return filtered_usage
        except Exception as e:
            raise Exception(f"Failed to retrieve usage data: {str(e)}")
    
    def get_price_history(self, site_id: str, start_date: datetime, end_date: datetime):
        """
        Get historical price data for a site between start and end dates.
        
        Args:
            site_id: The site ID to get prices for
            start_date: Start date for price data (timezone-aware)
            end_date: End date for price data (timezone-aware)
            
        Returns:
            List of price intervals filtered to the exact time range
        """
        try:
            # API works on daily boundaries, so get all data for the date range
            start_date_api = start_date.date()
            end_date_api = end_date.date()
            all_prices = self.client.get_prices(site_id, start_date=start_date_api, end_date=end_date_api)
            
            # Filter results to exact datetime range
            filtered_prices = []
            for price in all_prices:
                if hasattr(price, 'actual_instance') and price.actual_instance:
                    actual = price.actual_instance
                    # Check if nem_time is within the requested range
                    if start_date <= actual.nem_time <= end_date:
                        filtered_prices.append(price)
            
            return filtered_prices
        except Exception as e:
            raise Exception(f"Failed to retrieve price history: {str(e)}")
    
    def get_renewable_data(self, state: str = 'vic', next_hours: int = 24, previous_hours: int = 24):
        """
        Get renewable energy data for a state.
        
        Args:
            state: State code (nsw, sa, qld, vic)
            next_hours: Number of hours of forecast data
            previous_hours: Number of hours of historical data
            
        Returns:
            List of renewable energy intervals
        """
        try:
            # Calculate number of 30-minute intervals
            next_intervals = next_hours * 2
            previous_intervals = previous_hours * 2
            
            # Use the new v2.0.12 renewable endpoint
            return self.client.get_current_renewables(
                state=state,
                next=next_intervals,
                previous=previous_intervals,
                resolution=30
            )
                
        except Exception as e:
            raise Exception(f"Failed to retrieve renewable data: {str(e)}")
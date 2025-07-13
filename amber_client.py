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
            
        # Configure the API client following Graham Lea's pattern
        amber_configuration = amberelectric.Configuration(access_token=api_token)
        self.client = amber_api.AmberApi.create(amber_configuration)
    
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
            return self.client.get_current_price(site_id, next=next_intervals)
        except Exception as e:
            raise Exception(f"Failed to retrieve current prices: {str(e)}")
    
    def get_usage_data(self, site_id: str, start_date: datetime, end_date: datetime):
        """
        Get usage data for a site between start and end dates.
        
        Args:
            site_id: The site ID to get usage for
            start_date: Start date for usage data
            end_date: End date for usage data
            
        Returns:
            List of usage intervals
        """
        try:
            return self.client.get_usage(site_id, start_date=start_date, end_date=end_date)
        except Exception as e:
            raise Exception(f"Failed to retrieve usage data: {str(e)}")
    
    def get_price_history(self, site_id: str, start_date: datetime, end_date: datetime):
        """
        Get historical price data for a site between start and end dates.
        
        Args:
            site_id: The site ID to get prices for
            start_date: Start date for price data
            end_date: End date for price data
            
        Returns:
            List of price intervals
        """
        try:
            return self.client.get_prices(site_id, start_date=start_date, end_date=end_date)
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
            
            # Use the generic request method to access renewable endpoint
            path = f"/state/{state}/renewables/current"
            query_params = {
                'next': next_intervals,
                'previous': previous_intervals,
                'resolution': 30
            }
            
            response = self.client.request(
                method='GET',
                path=path,
                query_params=query_params
            )
            
            if response.status == 200:
                # Parse the bytes response as JSON
                import json
                if isinstance(response.data, bytes):
                    data_str = response.data.decode('utf-8')
                    return json.loads(data_str)
                elif isinstance(response.data, str):
                    return json.loads(response.data)
                else:
                    return response.data
            else:
                raise Exception(f"API returned status {response.status}")
                
        except Exception as e:
            raise Exception(f"Failed to retrieve renewable data: {str(e)}")
"""
Database service for Amber-Home Frontend Application.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import pytz
from config import Config

logger = logging.getLogger(__name__)


class DatabaseService:
    """Database operations service for frontend."""
    
    def __init__(self):
        self.connection: Optional[psycopg2.extensions.connection] = None
        self.timezone = pytz.timezone(Config.DISPLAY_TIMEZONE)
    
    def connect(self) -> psycopg2.extensions.connection:
        """Connect to PostgreSQL database."""
        try:
            # Use SSL for production, disable for local development
            if Config.is_production():
                conn = psycopg2.connect(Config.DATABASE_URL, sslmode='require')
            else:
                conn = psycopg2.connect(Config.DATABASE_URL, sslmode='disable')
            
            self.connection = conn
            logger.info("Connected to PostgreSQL database")
            return conn
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Database connection closed")
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """Execute SQL query and return results as DataFrame."""
        if not self.connection:
            self.connect()
        
        try:
            df = pd.read_sql_query(query, self.connection, params=params)
            return df
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    def get_price_data_today(self) -> pd.DataFrame:
        """Get price data for today in AEST timezone."""
        query = """
       SELECT 
           nem_time AT TIME ZONE 'Australia/Sydney' as aest_time,
           channel_type,
           per_kwh,
           spot_per_kwh,
           renewables,
           descriptor,
           spike_status
       FROM price_data 
       WHERE nem_time AT TIME ZONE 'Australia/Sydney' >= 
             (CURRENT_DATE AT TIME ZONE 'Australia/Sydney')::date
         AND nem_time AT TIME ZONE 'Australia/Sydney' < 
             (CURRENT_DATE AT TIME ZONE 'Australia/Sydney')::date + INTERVAL '1 day'
       ORDER BY nem_time ASC
       """
        return self.execute_query(query)

    def get_usage_data_24h(self) -> pd.DataFrame:
        """Get usage data for today in AEST timezone."""
        query = """
        SELECT 
            nem_time AT TIME ZONE 'Australia/Sydney' as aest_time,
            channel_id,
            channel_type,
            kwh,
            cost,
            quality
        FROM usage_data 
        WHERE nem_time AT TIME ZONE 'Australia/Sydney' >= 
              (CURRENT_DATE AT TIME ZONE 'Australia/Sydney')::date
          AND nem_time AT TIME ZONE 'Australia/Sydney' < 
              (CURRENT_DATE AT TIME ZONE 'Australia/Sydney')::date + INTERVAL '1 day'
        ORDER BY nem_time ASC
        """
        return self.execute_query(query)
    
    def get_cost_stats_7d(self) -> Dict[str, Any]:
        """Get cost statistics for the past 7 days in AEST timezone."""
        query = """
        SELECT 
            DATE(nem_time AT TIME ZONE 'Australia/Sydney') as date,
            SUM(CASE WHEN cost > 0 THEN cost/100 ELSE 0 END) as daily_cost_import,
            SUM(CASE WHEN cost < 0 THEN ABS(cost)/100 ELSE 0 END) as daily_cost_export,
            SUM(cost/100) as daily_cost_net,
            SUM(CASE WHEN kwh > 0 THEN kwh ELSE 0 END) as daily_kwh_import,
            SUM(CASE WHEN kwh < 0 THEN ABS(kwh) ELSE 0 END) as daily_kwh_export,
            COUNT(*) as record_count
        FROM usage_data 
        WHERE nem_time AT TIME ZONE 'Australia/Sydney' >= 
              (CURRENT_DATE AT TIME ZONE 'Australia/Sydney')::date - INTERVAL '7 days'
        GROUP BY DATE(nem_time AT TIME ZONE 'Australia/Sydney')
        ORDER BY date DESC
        """
        df = self.execute_query(query)
        
        if df.empty:
            return {
                'total_cost': 0,
                'avg_daily_cost': 0,
                'total_import_cost': 0,
                'total_export_cost': 0,
                'total_kwh_import': 0,
                'total_kwh_export': 0,
                'days_with_data': 0
            }
        
        return {
            'total_cost': df['daily_cost_net'].sum(),
            'avg_daily_cost': df['daily_cost_net'].mean(),
            'total_import_cost': df['daily_cost_import'].sum(),
            'total_export_cost': df['daily_cost_export'].sum(),
            'total_kwh_import': df['daily_kwh_import'].sum(),
            'total_kwh_export': df['daily_kwh_export'].sum(),
            'days_with_data': len(df),
            'daily_data': df
        }
    
    def get_latest_data_timestamp(self) -> Optional[datetime]:
        """Get the timestamp of the most recent data in AEST timezone."""
        query = """
        SELECT MAX(nem_time AT TIME ZONE 'Australia/Sydney') as latest_time
        FROM usage_data
        """
        df = self.execute_query(query)
        if df.empty or df['latest_time'].iloc[0] is None:
            return None
        return df['latest_time'].iloc[0]
    
    def get_forecast_data_10h(self) -> pd.DataFrame:
        """Get forecast price data for the next 10 hours in AEST timezone."""
        query = """
        SELECT 
            nem_time AT TIME ZONE 'Australia/Sydney' as aest_time,
            channel_type,
            per_kwh,
            spot_per_kwh,
            renewables,
            descriptor,
            spike_status,
            forecast_type,
            advanced_price_low,
            advanced_price_predicted,
            advanced_price_high,
            range_low,
            range_high
        FROM price_forecasts 
        WHERE nem_time AT TIME ZONE 'Australia/Sydney' >= 
              NOW() AT TIME ZONE 'Australia/Sydney'
          AND nem_time AT TIME ZONE 'Australia/Sydney' < 
              NOW() AT TIME ZONE 'Australia/Sydney' + INTERVAL '10 hours'
          AND forecast_generated_at = (
              SELECT MAX(forecast_generated_at) 
              FROM price_forecasts 
              WHERE forecast_generated_at >= NOW() - INTERVAL '2 hours'
          )
        ORDER BY nem_time ASC
        """
        return self.execute_query(query)
    
    def get_combined_historical_and_forecast_data(self) -> Dict[str, pd.DataFrame]:
        """Get both historical (today) and forecast (next 10h) price data."""
        historical_df = self.get_price_data_today()
        forecast_df = self.get_forecast_data_10h()
        
        return {
            'historical': historical_df,
            'forecast': forecast_df
        }
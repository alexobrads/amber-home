#!/usr/bin/env python3
"""
Automated Data Collection Service for Amber-Home

This service:
1. Initializes the database with historical data on first run
2. Runs continuous updates every 5 minutes to collect latest price and usage data
3. Handles Railway PostgreSQL connection and local testing
"""

import os
import time
import logging
import signal
import sys
from datetime import datetime, timedelta
from typing import Optional, List
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from amber_client import AmberClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper()),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self):
        self.amber_client = None
        self.db_connection = None
        self.sites = []
        self.running = True
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        logger.info("Received shutdown signal, stopping gracefully...")
        self.running = False
    
    def get_historical_start_date(self) -> datetime:
        """Get the start date for historical data collection"""
        start_date_str = os.getenv('HISTORICAL_START_DATE')
        
        if start_date_str:
            try:
                # Try to parse the date string (supports formats like 2024-01-01, 2024-01-01T00:00:00, etc.)
                return datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            except ValueError:
                try:
                    # Try simple date format YYYY-MM-DD
                    return datetime.strptime(start_date_str, '%Y-%m-%d')
                except ValueError:
                    logger.error(f"Invalid HISTORICAL_START_DATE format '{start_date_str}', use YYYY-MM-DD")
                    raise ValueError(f"Invalid date format: {start_date_str}")
        else:
            raise ValueError("HISTORICAL_START_DATE environment variable is required")
    
    def validate_env(self) -> None:
        """Validate required environment variables"""
        required_vars = ['AMBER_API_KEY', 'DATABASE_URL', 'HISTORICAL_START_DATE']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Validate date format
        try:
            self.get_historical_start_date()
        except ValueError as e:
            raise ValueError(f"Invalid HISTORICAL_START_DATE: {e}")
        
    def connect_db(self) -> psycopg2.extensions.connection:
        """Connect to PostgreSQL database using DATABASE_URL"""
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        try:
            # Use SSL for production (Railway), disable for local development
            if 'railway' in database_url or 'amazonaws' in database_url:
                conn = psycopg2.connect(database_url, sslmode='require')
            else:
                conn = psycopg2.connect(database_url, sslmode='disable')
            logger.info("Connected to PostgreSQL database")
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
            
    def init_amber_client(self) -> AmberClient:
        """Initialize Amber Electric API client"""
        api_key = os.getenv('AMBER_API_KEY')
        if not api_key:
            raise ValueError("AMBER_API_KEY environment variable is required")
        return AmberClient(api_key)
        
    def ensure_database_schema(self):
        """Ensure database schema exists"""
        # Try both container path and local path
        schema_paths = ['/app/schema.sql', './schema.sql']
        schema_sql = None
        
        for path in schema_paths:
            try:
                with open(path, 'r') as f:
                    schema_sql = f.read()
                logger.info(f"Found schema file at: {path}")
                break
            except FileNotFoundError:
                continue
        
        if not schema_sql:
            raise FileNotFoundError("Could not find schema.sql file")
            
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(schema_sql)
                self.db_connection.commit()
                logger.info("Database schema ensured")
        except psycopg2.errors.DuplicateObject as e:
            # Schema already exists, this is fine
            logger.info(f"Database schema already exists: {e}")
            self.db_connection.rollback()
        except Exception as e:
            logger.error(f"Failed to create database schema: {e}")
            self.db_connection.rollback()
            raise
            
    def collect_sites(self):
        """Collect and store site information"""
        try:
            sites = self.amber_client.get_sites()
            self.sites = sites
            
            with self.db_connection.cursor() as cursor:
                for site in sites:
                    # Handle API changes - network attribute may not exist
                    logger.info(f"Processing site {site.id} with NMI {site.nmi}")
                    
                    cursor.execute("""
                        INSERT INTO sites (id, nmi)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            nmi = EXCLUDED.nmi
                    """, (site.id, site.nmi))
                
                self.db_connection.commit()
                logger.info(f"Collected {len(sites)} sites")
                
        except Exception as e:
            logger.error(f"Failed to collect sites: {e}")
            raise
            
    def collect_price_data(self, start_date: datetime, end_date: datetime):
        """Collect price data for all sites"""
        for site in self.sites:
            try:
                current_start = start_date
                
                while current_start < end_date:
                    current_end = min(current_start + timedelta(days=7), end_date)
                    
                    logger.info(f"Collecting prices for site {site.id} from {current_start.date()} to {current_end.date()}")
                    
                    prices = self.amber_client.get_price_history(
                        site.id, 
                        current_start, 
                        current_end
                    )
                    
                    with self.db_connection.cursor() as cursor:
                        for price in prices:
                            cursor.execute("""
                                INSERT INTO price_data (
                                    site_id, nem_time, channel_type, per_kwh, spot_per_kwh, 
                                    renewables, spike_status
                                )
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (site_id, nem_time, channel_type) DO UPDATE SET
                                    per_kwh = EXCLUDED.per_kwh,
                                    spot_per_kwh = EXCLUDED.spot_per_kwh,
                                    renewables = EXCLUDED.renewables,
                                    spike_status = EXCLUDED.spike_status
                            """, (
                                site.id,
                                price.nem_time,
                                str(price.channel_type),  # Convert enum to string
                                price.per_kwh,
                                price.spot_per_kwh,
                                price.renewables,
                                str(getattr(price, 'spike_status', None)) if getattr(price, 'spike_status', None) else None
                            ))
                    
                    self.db_connection.commit()
                    current_start = current_end
                    
                    # Rate limiting
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"Failed to collect price data for site {site.id}: {e}")
                continue
                
    def collect_usage_data(self, start_date: datetime, end_date: datetime):
        """Collect usage data for all sites"""
        for site in self.sites:
            try:
                current_start = start_date
                
                while current_start < end_date:
                    current_end = min(current_start + timedelta(days=7), end_date)
                    
                    logger.info(f"Collecting usage for site {site.id} from {current_start.date()} to {current_end.date()}")
                    
                    usage_data = self.amber_client.get_usage_data(
                        site.id,
                        current_start,
                        current_end
                    )
                    
                    with self.db_connection.cursor() as cursor:
                        logger.info(f"Got {len(usage_data)} usage records for site {site.id}")
                        for usage in usage_data:
                            # Get raw channel_id from API (may be None)
                            channel_id = getattr(usage, 'channelIdentifier', None)
                            
                            # Store raw API data without filtering or modifications
                            cursor.execute("""
                                INSERT INTO usage_data (
                                    site_id, nem_time, channel_id, channel_type, kwh, 
                                    cost, quality
                                )
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (site_id, nem_time, channel_id) DO UPDATE SET
                                    kwh = EXCLUDED.kwh,
                                    cost = EXCLUDED.cost,
                                    quality = EXCLUDED.quality
                            """, (
                                site.id,
                                usage.nem_time,
                                channel_id,
                                str(usage.channel_type),  # Convert enum to string
                                usage.kwh,
                                usage.cost,  # Raw cost from API (in cents)
                                usage.quality
                            ))
                    
                    self.db_connection.commit()
                    current_start = current_end
                    
                    # Rate limiting
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"Failed to collect usage data for site {site.id}: {e}")
                continue
                
    def is_initialized(self) -> bool:
        """Check if database has been initialized with data"""
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM sites")
                site_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM price_data")
                price_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM usage_data")
                usage_count = cursor.fetchone()[0]
                
                # Check if we have data from the configured start date
                start_date = self.get_historical_start_date()
                cursor.execute("""
                    SELECT COUNT(*) FROM price_data 
                    WHERE nem_time >= %s
                """, (start_date,))
                price_from_start = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) FROM usage_data 
                    WHERE nem_time >= %s
                """, (start_date,))
                usage_from_start = cursor.fetchone()[0]
                
                has_sites = site_count > 0
                has_data_from_start = price_from_start > 0 and usage_from_start > 0
                
                if has_sites and has_data_from_start:
                    logger.info(f"Database initialized with {site_count} sites, {price_count} price records, {usage_count} usage records from {start_date}")
                    return True
                else:
                    logger.info(f"Database not fully initialized - sites: {site_count}, price from start: {price_from_start}, usage from start: {usage_from_start}")
                    return False
                
        except Exception as e:
            logger.error(f"Error checking initialization: {e}")
            return False
            
    def get_latest_data_date(self) -> Optional[datetime]:
        """Get the date of the most recent data"""
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute("""
                    SELECT MAX(GREATEST(
                        COALESCE((SELECT MAX(nem_time) FROM price_data), NULL),
                        COALESCE((SELECT MAX(nem_time) FROM usage_data), NULL)
                    )) as latest_date
                """)
                result = cursor.fetchone()
                latest_date = result[0] if result and result[0] else None
                
                # Return the latest timestamp or None
                return latest_date
                
        except Exception as e:
            logger.error(f"Failed to get latest data date: {e}")
            return None
            
    def collect_data_from_date(self, start_date: datetime):
        """Collect data from a specific date to now"""
        end_date = datetime.now()
        
        # Ensure both dates are timezone-aware or naive
        if start_date.tzinfo is not None and end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=start_date.tzinfo)
        elif start_date.tzinfo is None and end_date.tzinfo is not None:
            start_date = start_date.replace(tzinfo=end_date.tzinfo)
        
        logger.info(f"Collecting data from {start_date} to {end_date}")
        
        # Ensure start_date is not in the future
        if start_date > end_date:
            logger.warning(f"Start date {start_date} is in the future, using current date")
            start_date = end_date - timedelta(days=1)
        
        # Collect price data
        self.collect_price_data(start_date, end_date)
        
        # Collect usage data
        self.collect_usage_data(start_date, end_date)
        
        logger.info("Data collection completed")
        
    def update_latest_data(self):
        """Update with latest data since last collection"""
        logger.info("Updating latest data...")
        
        # Get the most recent data date we have
        latest_date = self.get_latest_data_date()
        
        if latest_date:
            # Start from the latest timestamp to ensure no gaps
            start_date = latest_date - timedelta(hours=1)
            logger.info(f"Found existing data, collecting from {start_date}")
        else:
            # No data yet, start from configured start date
            start_date = self.get_historical_start_date()
            logger.info(f"No existing data found, collecting from configured start date {start_date}")
        
        self.collect_data_from_date(start_date)
        
    def run(self):
        """Main service loop"""
        logger.info("Starting Amber-Home Data Collector...")
        
        try:
            # Validate required environment variables
            self.validate_env()
            
            # Initialize connections
            self.amber_client = self.init_amber_client()
            self.db_connection = self.connect_db()
            
            # Ensure database schema
            self.ensure_database_schema()
            
            # Collect sites first
            self.collect_sites()
            
            # Check if we should force reinitialization
            force_reinit = os.getenv('FORCE_REINIT', '').lower() == 'true'
            
            # Initialize if needed or forced
            if force_reinit or not self.is_initialized():
                if force_reinit:
                    logger.info("FORCE_REINIT=true, running full historical data collection...")
                else:
                    logger.info("Database not fully initialized, running historical data collection...")
                start_date = self.get_historical_start_date()
                logger.info(f"Collecting all data from start date: {start_date}")
                self.collect_data_from_date(start_date)
            else:
                logger.info("Database already initialized, starting regular updates...")
                # Still run one update to catch up on any missing recent data
                self.update_latest_data()
                
            # Main update loop
            while self.running:
                try:
                    self.update_latest_data()
                    
                    # Wait for configured interval before next update
                    interval_minutes = int(os.getenv('COLLECTION_INTERVAL_MINUTES', '5'))
                    interval_seconds = interval_minutes * 60
                    for _ in range(interval_seconds):
                        if not self.running:
                            break
                        time.sleep(1)
                        
                except Exception as e:
                    logger.error(f"Error during data update: {e}")
                    # Wait 1 minute before retrying
                    time.sleep(60)
                    
        except Exception as e:
            logger.error(f"Fatal error in data collector: {e}")
            raise
        finally:
            if self.db_connection:
                self.db_connection.close()
                logger.info("Database connection closed")
                
        logger.info("Data collector stopped")

if __name__ == "__main__":
    collector = DataCollector()
    collector.run()
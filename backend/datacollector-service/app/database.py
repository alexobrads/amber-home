"""
Database service for Amber-Home application.
"""

import logging
from datetime import datetime
from typing import Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor
from .config import Config

logger = logging.getLogger(__name__)


class DatabaseService:
    """Database operations service."""
    
    def __init__(self):
        self.connection: Optional[psycopg2.extensions.connection] = None
    
    def connect(self) -> psycopg2.extensions.connection:
        """Connect to PostgreSQL database."""
        if not Config.DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required")
        
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
    
    def ensure_schema(self) -> None:
        """Ensure database schema exists."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        
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
            with self.connection.cursor() as cursor:
                # Split schema into individual statements
                statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
                
                for statement in statements:
                    try:
                        cursor.execute(statement)
                        self.connection.commit()
                    except (psycopg2.errors.DuplicateObject, psycopg2.errors.DuplicateTable):
                        # Already exists, rollback and continue
                        self.connection.rollback()
                        continue
                    except Exception as e:
                        # Other error, rollback and continue (don't fail)
                        logger.warning(f"Schema statement failed (continuing): {e}")
                        self.connection.rollback()
                        continue
                
                logger.info("Database schema ensured")
                
        except Exception as e:
            logger.error(f"Failed to create database schema: {e}")
            self.connection.rollback()
            raise
    
    def get_site_count(self) -> int:
        """Get count of sites in database."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM sites")
            return cursor.fetchone()[0]
    
    def get_latest_price_date(self) -> Optional[datetime]:
        """Get the date of the most recent price data in NEM time."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        try:
            from zoneinfo import ZoneInfo
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT MAX(nem_time) FROM price_data")
                result = cursor.fetchone()
                if result and result[0]:
                    # Ensure the datetime is timezone-aware in NEM time
                    dt = result[0]
                    if dt.tzinfo is None:
                        # If naive, assume it's already in NEM time
                        aest = ZoneInfo("Australia/Sydney")
                        return dt.replace(tzinfo=aest)
                    else:
                        # If timezone-aware, convert to NEM time
                        aest = ZoneInfo("Australia/Sydney")
                        return dt.astimezone(aest)
                return None
        except Exception as e:
            logger.error(f"Failed to get latest price date: {e}")
            return None
    
    def get_latest_usage_date(self) -> Optional[datetime]:
        """Get the date of the most recent usage data in NEM time."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        try:
            from zoneinfo import ZoneInfo
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT MAX(nem_time) FROM usage_data")
                result = cursor.fetchone()
                if result and result[0]:
                    # Ensure the datetime is timezone-aware in NEM time
                    dt = result[0]
                    if dt.tzinfo is None:
                        # If naive, assume it's already in NEM time
                        aest = ZoneInfo("Australia/Sydney")
                        return dt.replace(tzinfo=aest)
                    else:
                        # If timezone-aware, convert to NEM time
                        aest = ZoneInfo("Australia/Sydney")
                        return dt.astimezone(aest)
                return None
        except Exception as e:
            logger.error(f"Failed to get latest usage date: {e}")
            return None
    
    def is_initialized(self) -> bool:
        """Check if database has been initialized with data."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        try:
            start_date = Config.get_historical_start_date()
            
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM sites")
                site_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM price_data WHERE nem_time >= %s", (start_date,))
                price_from_start = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM usage_data WHERE nem_time >= %s", (start_date,))
                usage_from_start = cursor.fetchone()[0]
                
                has_sites = site_count > 0
                has_data_from_start = price_from_start > 0 and usage_from_start > 0
                
                if has_sites and has_data_from_start:
                    logger.info(f"Database initialized with {site_count} sites, {price_from_start} price records, {usage_from_start} usage records from {start_date}")
                    return True
                else:
                    logger.info(f"Database not fully initialized - sites: {site_count}, price from start: {price_from_start}, usage from start: {usage_from_start}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error checking initialization: {e}")
            return False
    
    def insert_sites(self, sites: List) -> None:
        """Insert sites into database."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        with self.connection.cursor() as cursor:
            for site in sites:
                cursor.execute("""
                    INSERT INTO sites (id, nmi)
                    VALUES (%s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        nmi = EXCLUDED.nmi
                """, (site.id, site.nmi))
            
            self.connection.commit()
            logger.info(f"Inserted {len(sites)} sites")
    
    def insert_price_data(self, site_id: str, prices: List) -> None:
        """Insert price data into database."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        with self.connection.cursor() as cursor:
            for price in prices:
                # Handle new SDK v2.0.12 structure - get actual instance
                price_data = price.actual_instance if hasattr(price, 'actual_instance') else price
                
                cursor.execute("""
                    INSERT INTO price_data (
                        site_id, nem_time, start_time, end_time, duration, channel_type, 
                        per_kwh, spot_per_kwh, renewables, spike_status, descriptor, 
                        estimate, var_date
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (site_id, nem_time, channel_type) DO UPDATE SET
                        per_kwh = EXCLUDED.per_kwh,
                        spot_per_kwh = EXCLUDED.spot_per_kwh,
                        renewables = EXCLUDED.renewables,
                        spike_status = EXCLUDED.spike_status,
                        descriptor = EXCLUDED.descriptor,
                        estimate = EXCLUDED.estimate
                """, (
                    site_id,
                    price_data.nem_time,
                    getattr(price_data, 'start_time', None),
                    getattr(price_data, 'end_time', None),
                    getattr(price_data, 'duration', None),
                    str(price_data.channel_type),
                    price_data.per_kwh,
                    price_data.spot_per_kwh,
                    price_data.renewables,
                    str(getattr(price_data, 'spike_status', None)) if getattr(price_data, 'spike_status', None) else None,
                    str(getattr(price_data, 'descriptor', None)) if getattr(price_data, 'descriptor', None) else None,
                    getattr(price_data, 'estimate', False),
                    getattr(price_data, 'var_date', None)
                ))
        
        self.connection.commit()
    
    def insert_usage_data(self, site_id: str, usage_data: List) -> None:
        """Insert usage data into database."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        with self.connection.cursor() as cursor:
            for usage in usage_data:
                # Get raw channel_id from API - now available as channel_identifier
                channel_id = getattr(usage, 'channel_identifier', None)
                
                cursor.execute("""
                    INSERT INTO usage_data (
                        site_id, nem_time, start_time, end_time, duration, channel_id, 
                        channel_type, kwh, cost, quality, descriptor, var_date
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (site_id, nem_time, channel_id) DO UPDATE SET
                        kwh = EXCLUDED.kwh,
                        cost = EXCLUDED.cost,
                        quality = EXCLUDED.quality,
                        descriptor = EXCLUDED.descriptor
                """, (
                    site_id,
                    usage.nem_time,
                    getattr(usage, 'start_time', None),
                    getattr(usage, 'end_time', None),
                    getattr(usage, 'duration', None),
                    channel_id,
                    str(usage.channel_type),
                    usage.kwh,
                    usage.cost,
                    usage.quality,
                    str(getattr(usage, 'descriptor', None)) if getattr(usage, 'descriptor', None) else None,
                    getattr(usage, 'var_date', None)
                ))
        
        self.connection.commit()
    

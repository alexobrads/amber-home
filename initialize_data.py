#!/usr/bin/env python3
"""
Amber-Home One-Time Data Initialization Script

This script performs a complete initial setup:
1. Collects and stores site information
2. Discovers the earliest available data date
3. Collects all historical price and usage data in 7-day chunks
4. Provides progress updates and final summary

Run this once to populate your database with all available historical data.
"""

import os
import time
import argparse
from datetime import datetime, timedelta
from typing import Optional, Tuple
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from amber_client import AmberClient

# Load environment variables
load_dotenv()


def connect_db(host: str = "localhost", port: int = 5432, database: str = "amber_home", 
               user: str = "amber_user", password: str = "amber_password") -> psycopg2.extensions.connection:
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        print("Make sure PostgreSQL container is running: docker-compose up -d")
        raise


def get_api_client() -> AmberClient:
    """Get configured Amber API client"""
    api_key = os.getenv('AMBER_API_KEY')
    if not api_key:
        raise ValueError("AMBER_API_KEY environment variable not set")
    return AmberClient(api_key)


def collect_sites(conn: psycopg2.extensions.connection) -> str:
    """Collect and store site information, return the site ID"""
    print("🏠 Collecting site information...")
    
    client = get_api_client()
    sites = client.get_sites()
    
    if not sites:
        raise Exception("No sites found for your Amber account")
    
    with conn.cursor() as cursor:
        # Clear existing sites and insert new ones
        cursor.execute("DELETE FROM sites")
        
        for site in sites:
            cursor.execute("""
                INSERT INTO sites (id, nmi)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    nmi = EXCLUDED.nmi
            """, (
                site.id,
                site.nmi
            ))
    
    site_id = sites[0].id
    print(f"✅ Found site: {site_id} (NMI: {sites[0].nmi})")
    return site_id


def discover_data_start_date(site_id: str) -> Optional[str]:
    """Find the earliest date with available data by testing different periods"""
    print("🔍 Discovering earliest available data...")
    
    client = get_api_client()
    
    # Test periods going back in time
    test_dates = [
        ("2025-07-01", "2025-07-07"),  # Recent
        ("2025-06-01", "2025-06-07"),  # Last month
        ("2025-05-01", "2025-05-07"),  # Two months ago
        ("2025-04-01", "2025-04-07"),  # Three months ago
        ("2025-03-01", "2025-03-07"),  # Four months ago
        ("2025-02-01", "2025-02-07"),  # Five months ago
        ("2025-01-01", "2025-01-07"),  # Start of year
        ("2024-12-01", "2024-12-07"),  # Last year
        ("2024-06-01", "2024-06-07"),  # Mid last year
        ("2024-01-01", "2024-01-07"),  # Start of last year
    ]
    
    earliest_with_data = None
    
    for start_date, end_date in test_dates:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Test price data availability
            price_data = client.get_price_history(site_id, start_dt, end_dt)
            
            if price_data and len(price_data) > 0:
                print(f"  ✅ Data available for {start_date}")
                earliest_with_data = start_date
            else:
                print(f"  ❌ No data for {start_date}")
                
        except Exception as e:
            print(f"  ❌ Error testing {start_date}: {e}")
    
    if earliest_with_data:
        print(f"🎯 Earliest data found: {earliest_with_data}")
        return earliest_with_data
    else:
        print("⚠️  No historical data found, will collect from today")
        return datetime.now().strftime('%Y-%m-%d')


def collect_historical_data(site_id: str, start_date: str, end_date: str, 
                          conn: psycopg2.extensions.connection) -> Tuple[int, int]:
    """Collect all historical data in 7-day chunks"""
    print(f"📊 Collecting historical data from {start_date} to {end_date}")
    print("This will make multiple API calls in 7-day chunks (API limit)...")
    
    client = get_api_client()
    
    # Parse dates
    current_date = datetime.strptime(start_date, '%Y-%m-%d')
    final_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    total_price_records = 0
    total_usage_records = 0
    chunk_count = 0
    
    while current_date < final_date:
        # Calculate chunk end date (7 days later or final date)
        chunk_end = min(current_date + timedelta(days=6), final_date)
        
        chunk_start_str = current_date.strftime('%Y-%m-%d')
        chunk_end_str = chunk_end.strftime('%Y-%m-%d')
        
        chunk_count += 1
        print(f"\n📅 Chunk {chunk_count}: {chunk_start_str} to {chunk_end_str}")
        
        try:
            # Collect prices for this chunk
            print("  💰 Collecting prices...", end=" ")
            price_before = get_record_count(conn, "price_data")
            
            start_dt = datetime.strptime(chunk_start_str, '%Y-%m-%d')
            end_dt = datetime.strptime(chunk_end_str, '%Y-%m-%d')
            price_data = client.get_price_history(site_id, start_dt, end_dt)
            
            # Store price data
            price_inserted = 0
            with conn.cursor() as cursor:
                for interval in price_data:
                    cursor.execute("""
                        INSERT INTO price_data (
                            site_id, nem_time, channel_type, per_kwh, spot_per_kwh, 
                            renewables, spike_status, date
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (site_id, nem_time, channel_type) DO NOTHING
                    """, (
                        site_id,
                        interval.nem_time,
                        str(interval.channel_type),
                        float(interval.per_kwh),
                        float(interval.spot_per_kwh),
                        float(interval.renewables) if interval.renewables else None,
                        str(interval.spike_status),
                        interval.date
                    ))
                    if cursor.rowcount > 0:
                        price_inserted += 1
            
            print(f"{price_inserted} inserted")
            
            # Collect usage for this chunk
            print("  ⚡ Collecting usage...", end=" ")
            usage_data = client.get_usage_data(site_id, start_dt, end_dt)
            
            # Store usage data
            usage_inserted = 0
            with conn.cursor() as cursor:
                for interval in usage_data:
                    channel_id = getattr(interval, 'channel_identifier', 
                                       getattr(interval, 'channelIdentifier', 'unknown'))
                    
                    cursor.execute("""
                        INSERT INTO usage_data (
                            site_id, nem_time, channel_id, channel_type, kwh, 
                            cost_dollars, quality, date
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (site_id, nem_time, channel_id) DO NOTHING
                    """, (
                        site_id,
                        interval.nem_time,
                        channel_id,
                        str(interval.channel_type),
                        float(interval.kwh),
                        float(interval.cost) / 100,  # Convert cents to dollars
                        interval.quality,
                        interval.date
                    ))
                    if cursor.rowcount > 0:
                        usage_inserted += 1
            
            print(f"{usage_inserted} inserted")
            
            total_price_records += price_inserted
            total_usage_records += usage_inserted
            
            # Small delay to be respectful to the API
            if chunk_count % 5 == 0:
                print("  ⏸️  Pausing to respect API limits...")
                time.sleep(2)
            else:
                time.sleep(0.5)
                
        except Exception as e:
            print(f"  ❌ Error processing chunk: {e}")
            # Continue with next chunk
        
        # Move to next chunk
        current_date = chunk_end + timedelta(days=1)
    
    return total_price_records, total_usage_records


def get_record_count(conn: psycopg2.extensions.connection, table_name: str) -> int:
    """Get the current number of records in a table"""
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]


def show_final_summary(conn: psycopg2.extensions.connection):
    """Show final data summary"""
    print("\n" + "="*50)
    print("🎉 INITIALIZATION COMPLETE")
    print("="*50)
    
    with conn.cursor() as cursor:
        # Sites summary
        cursor.execute("SELECT COUNT(*) FROM sites")
        site_count = cursor.fetchone()[0]
        print(f"🏠 Sites: {site_count}")
        
        # Price data summary
        cursor.execute("""
            SELECT COUNT(*), MIN(date), MAX(date), COUNT(DISTINCT channel_type) 
            FROM price_data
        """)
        price_stats = cursor.fetchone()
        if price_stats[0] > 0:
            print(f"💰 Price records: {price_stats[0]:,}")
            print(f"   Date range: {price_stats[1]} to {price_stats[2]}")
            print(f"   Channels: {price_stats[3]}")
        
        # Usage data summary
        cursor.execute("""
            SELECT COUNT(*), MIN(date), MAX(date), COUNT(DISTINCT channel_id) 
            FROM usage_data
        """)
        usage_stats = cursor.fetchone()
        if usage_stats[0] > 0:
            print(f"⚡ Usage records: {usage_stats[0]:,}")
            print(f"   Date range: {usage_stats[1]} to {usage_stats[2]}")
            print(f"   Channels: {usage_stats[3]}")
        
        # Recent costs
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN cost_dollars > 0 THEN cost_dollars ELSE 0 END) as consumption_cost,
                SUM(CASE WHEN cost_dollars < 0 THEN ABS(cost_dollars) ELSE 0 END) as generation_credit
            FROM usage_data 
            WHERE date = (SELECT MAX(date) FROM usage_data)
        """)
        costs = cursor.fetchone()
        if costs and costs[0]:
            print(f"💵 Latest day cost: ${costs[0]:.2f} consumed, ${costs[1]:.2f} credit")
    
    print("\n✅ Your amber-home database is ready!")
    print("🚀 Next steps:")
    print("   • Run the dashboard: uv run streamlit run dashboard.py")
    print("   • Query data: uv run query_data.py --summary")
    print("   • Update data: uv run collect_data.py --type prices --start YYYY-MM-DD --end YYYY-MM-DD")


def main():
    """Main initialization process"""
    parser = argparse.ArgumentParser(description="Initialize Amber-Home database with all historical data")
    parser.add_argument("--start-date", help="Override automatic start date discovery (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date for collection (YYYY-MM-DD), defaults to today")
    parser.add_argument("--host", default="localhost", help="PostgreSQL host")
    parser.add_argument("--port", default=5432, type=int, help="PostgreSQL port")
    parser.add_argument("--db", default="amber_home", help="Database name")
    parser.add_argument("--user", default="amber_user", help="Database user")
    parser.add_argument("--password", default="amber_password", help="Database password")
    
    args = parser.parse_args()
    
    print("🚀 Amber-Home Database Initialization")
    print("=" * 40)
    
    try:
        # Connect to database
        print("🔌 Connecting to database...")
        conn = connect_db(args.host, args.port, args.db, args.user, args.password)
        
        # Step 1: Collect sites
        site_id = collect_sites(conn)
        
        # Step 2: Determine date range
        if args.start_date:
            start_date = args.start_date
            print(f"📅 Using provided start date: {start_date}")
        else:
            start_date = discover_data_start_date(site_id)
        
        end_date = args.end_date or datetime.now().strftime('%Y-%m-%d')
        
        # Step 3: Collect all historical data
        total_price, total_usage = collect_historical_data(site_id, start_date, end_date, conn)
        
        # Step 4: Show summary
        show_final_summary(conn)
        
        conn.close()
        return 0
        
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
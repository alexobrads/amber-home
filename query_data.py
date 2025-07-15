#!/usr/bin/env python3
"""
Amber-Home Query Helper

Simple script to query and analyze your home energy data.
"""

import os
import argparse
import psycopg2
import pandas as pd
from typing import List, Dict, Any
from dotenv import load_dotenv

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
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        print("Make sure PostgreSQL container is running: docker-compose up -d")
        return None


def run_query(sql: str, host: str = "localhost", port: int = 5432, database: str = "amber_home",
              user: str = "amber_user", password: str = "amber_password") -> pd.DataFrame:
    """Execute SQL query and return results as DataFrame"""
    conn = connect_db(host, port, database, user, password)
    if not conn:
        return None
    
    try:
        result = pd.read_sql(sql, conn)
        conn.close()
        return result
    except Exception as e:
        print(f"Query error: {e}")
        conn.close()
        return None


def show_summary(host: str = "localhost", port: int = 5432, database: str = "amber_home",
                 user: str = "amber_user", password: str = "amber_password") -> None:
    """Show comprehensive data summary"""
    conn = connect_db(host, port, database, user, password)
    if not conn:
        return
    
    print("=== Amber-Home Data Summary ===\n")
    
    # Sites
    print("📍 Sites:")
    sites = pd.read_sql("SELECT id, nmi FROM sites", conn)
    if not sites.empty:
        for _, site in sites.iterrows():
            print(f"  • {site['id']} (NMI: {site['nmi']})")
    else:
        print("  No sites found")
    
    print()
    
    # Price data summary
    print("💰 Price Data:")
    price_summary = pd.read_sql("""
        SELECT 
            COUNT(*) as records,
            MIN(date) as first_date,
            MAX(date) as last_date,
            COUNT(DISTINCT site_id) as sites,
            COUNT(DISTINCT channel_type) as channels
        FROM price_data
    """, conn).iloc[0]
    
    if price_summary['records'] > 0:
        print(f"  • {price_summary['records']:,} records")
        print(f"  • Date range: {price_summary['first_date']} to {price_summary['last_date']}")
        print(f"  • Sites: {price_summary['sites']}, Channels: {price_summary['channels']}")
        
        # Recent prices
        recent_prices = pd.read_sql("""
            SELECT channel_type, per_kwh, spot_per_kwh, renewables
            FROM price_data 
            WHERE date = (SELECT MAX(date) FROM price_data)
            ORDER BY nem_time DESC
            LIMIT 3
        """, conn)
        
        if not recent_prices.empty:
            print("  • Recent prices:")
            for _, price in recent_prices.iterrows():
                print(f"    - {price['channel_type']}: {price['per_kwh']:.2f}¢/kWh (spot: {price['spot_per_kwh']:.2f}¢/kWh, renewables: {price['renewables']:.1f}%)")
    else:
        print("  No price data found")
    
    print()
    
    # Usage data summary
    print("⚡ Usage Data:")
    usage_summary = pd.read_sql("""
        SELECT 
            COUNT(*) as records,
            MIN(date) as first_date,
            MAX(date) as last_date,
            COUNT(DISTINCT site_id) as sites,
            COUNT(DISTINCT channel_id) as channels
        FROM usage_data
    """, conn).iloc[0]
    
    if usage_summary['records'] > 0:
        print(f"  • {usage_summary['records']:,} records")
        print(f"  • Date range: {usage_summary['first_date']} to {usage_summary['last_date']}")
        print(f"  • Sites: {usage_summary['sites']}, Channels: {usage_summary['channels']}")
        
        # Recent usage summary
        recent_usage = pd.read_sql("""
            SELECT 
                channel_id,
                SUM(CASE WHEN kwh > 0 THEN kwh ELSE 0 END) as consumption_kwh,
                SUM(CASE WHEN kwh < 0 THEN ABS(kwh) ELSE 0 END) as generation_kwh,
                SUM(CASE WHEN cost_dollars > 0 THEN cost_dollars ELSE 0 END) as consumption_cost,
                SUM(CASE WHEN cost_dollars < 0 THEN ABS(cost_dollars) ELSE 0 END) as generation_credit
            FROM usage_data 
            WHERE date = (SELECT MAX(date) FROM usage_data)
            GROUP BY channel_id
        """, conn)
        
        if not recent_usage.empty:
            print("  • Latest day summary:")
            for _, usage in recent_usage.iterrows():
                print(f"    - {usage['channel_id']}: {usage['consumption_kwh']:.2f} kWh consumed, {usage['generation_kwh']:.2f} kWh generated")
                print(f"      Cost: ${usage['consumption_cost']:.2f}, Credit: ${usage['generation_credit']:.2f}")
    else:
        print("  No usage data found")
    
    conn.close()


def show_cost_analysis(days: int = 7, host: str = "localhost", port: int = 5432, 
                       database: str = "amber_home", user: str = "amber_user", 
                       password: str = "amber_password") -> None:
    """Show cost analysis for recent days"""
    conn = connect_db(host, port, database, user, password)
    if not conn:
        return
    
    print(f"=== Cost Analysis (Last {days} Days) ===\n")
    
    daily_costs = pd.read_sql(f"""
        SELECT 
            date,
            channel_id,
            SUM(CASE WHEN kwh > 0 THEN kwh ELSE 0 END) as consumption_kwh,
            SUM(CASE WHEN kwh < 0 THEN ABS(kwh) ELSE 0 END) as generation_kwh,
            SUM(CASE WHEN cost_dollars > 0 THEN cost_dollars ELSE 0 END) as consumption_cost,
            SUM(CASE WHEN cost_dollars < 0 THEN ABS(cost_dollars) ELSE 0 END) as generation_credit,
            SUM(cost_dollars) as net_cost
        FROM usage_data 
        WHERE date >= CURRENT_DATE - INTERVAL '{days} days'
        GROUP BY date, channel_id
        ORDER BY date DESC, channel_id
    """, conn)
    
    if not daily_costs.empty:
        for _, day in daily_costs.iterrows():
            print(f"{day['date']} - {day['channel_id']}:")
            print(f"  Consumption: {day['consumption_kwh']:.2f} kWh → ${day['consumption_cost']:.2f}")
            if day['generation_kwh'] > 0:
                print(f"  Generation: {day['generation_kwh']:.2f} kWh → ${day['generation_credit']:.2f} credit")
            print(f"  Net cost: ${day['net_cost']:.2f}")
            print()
        
        # Weekly totals
        totals = daily_costs.groupby('channel_id').agg({
            'consumption_kwh': 'sum',
            'generation_kwh': 'sum', 
            'consumption_cost': 'sum',
            'generation_credit': 'sum',
            'net_cost': 'sum'
        })
        
        print("Weekly Totals:")
        for channel_id in totals.index:
            row = totals.loc[channel_id]
            print(f"  {channel_id}:")
            print(f"    Consumption: {row['consumption_kwh']:.2f} kWh → ${row['consumption_cost']:.2f}")
            if row['generation_kwh'] > 0:
                print(f"    Generation: {row['generation_kwh']:.2f} kWh → ${row['generation_credit']:.2f} credit")
            print(f"    Net cost: ${row['net_cost']:.2f}")
    else:
        print("No usage data found for the specified period")
    
    conn.close()


def show_price_trends(days: int = 7, host: str = "localhost", port: int = 5432,
                      database: str = "amber_home", user: str = "amber_user", 
                      password: str = "amber_password") -> None:
    """Show price trends and statistics"""
    conn = connect_db(host, port, database, user, password)
    if not conn:
        return
    
    print(f"=== Price Trends (Last {days} Days) ===\n")
    
    price_stats = pd.read_sql(f"""
        SELECT 
            channel_type,
            COUNT(*) as intervals,
            AVG(per_kwh) as avg_price,
            MIN(per_kwh) as min_price,
            MAX(per_kwh) as max_price,
            AVG(spot_per_kwh) as avg_spot_price,
            AVG(renewables) as avg_renewables,
            SUM(CASE WHEN spike_status = 'spike' THEN 1 ELSE 0 END) as spike_intervals
        FROM price_data 
        WHERE date >= CURRENT_DATE - INTERVAL '{days} days'
        GROUP BY channel_type
    """, conn)
    
    if not price_stats.empty:
        for _, stats in price_stats.iterrows():
            print(f"{stats['channel_type']} Channel:")
            print(f"  Intervals: {stats['intervals']}")
            print(f"  Price range: {stats['min_price']:.2f}¢ - {stats['max_price']:.2f}¢/kWh")
            print(f"  Average price: {stats['avg_price']:.2f}¢/kWh")
            print(f"  Average spot price: {stats['avg_spot_price']:.2f}¢/kWh")
            print(f"  Average renewables: {stats['avg_renewables']:.1f}%")
            if stats['spike_intervals'] > 0:
                print(f"  Spike intervals: {stats['spike_intervals']}")
            print()
    else:
        print("No price data found for the specified period")
    
    conn.close()


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Amber-Home Data Query Tool")
    parser.add_argument("--summary", action="store_true", help="Show data summary")
    parser.add_argument("--costs", type=int, metavar="DAYS", help="Show cost analysis for N days")
    parser.add_argument("--prices", type=int, metavar="DAYS", help="Show price trends for N days") 
    parser.add_argument("--sql", help="Execute custom SQL query")
    parser.add_argument("--host", default="localhost", help="PostgreSQL host")
    parser.add_argument("--port", default=5432, type=int, help="PostgreSQL port")
    parser.add_argument("--db", default="amber_home", help="Database name")
    parser.add_argument("--user", default="amber_user", help="Database user")
    parser.add_argument("--password", default="amber_password", help="Database password")
    
    args = parser.parse_args()
    
    try:
        if args.summary:
            show_summary(args.host, args.port, args.db, args.user, args.password)
            
        elif args.costs:
            show_cost_analysis(args.costs, args.host, args.port, args.db, args.user, args.password)
            
        elif args.prices:
            show_price_trends(args.prices, args.host, args.port, args.db, args.user, args.password)
            
        elif args.sql:
            result = run_query(args.sql, args.host, args.port, args.db, args.user, args.password)
            if result is not None:
                print(result.to_string(index=False))
                
        else:
            # Default to summary
            show_summary(args.host, args.port, args.db, args.user, args.password)
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
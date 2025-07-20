"""
Main Streamlit application for Amber-Home Frontend.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import pytz
import logging
from config import Config
from database import DatabaseService
from components.price_charts import create_price_chart, display_price_summary, create_price_chart_with_forecasts
from components.usage_charts import create_usage_chart, display_usage_summary
from components.cost_stats import display_cost_stats, create_daily_cost_chart, create_usage_breakdown_chart

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title=Config.APP_TITLE,
    page_icon=Config.PAGE_ICON,
    layout=Config.LAYOUT,
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        padding: 1rem 0;
        margin-bottom: 2rem;
        border-bottom: 2px solid #e0e0e0;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .last-updated {
        color: #6c757d;
        font-size: 0.9rem;
        text-align: right;
    }
    .section-divider {
        margin: 2rem 0;
        border-top: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database service
@st.cache_resource
def init_database():
    """Initialize database connection."""
    return DatabaseService()

# Cache data for performance
@st.cache_data(ttl=Config.AUTO_REFRESH_SECONDS)
def load_price_data():
    """Load price data with caching."""
    db = init_database()
    try:
        return db.get_price_data_today()
    except Exception as e:
        logger.error(f"Error loading price data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=Config.AUTO_REFRESH_SECONDS)
def load_usage_data():
    """Load usage data with caching."""
    db = init_database()
    try:
        return db.get_usage_data_24h()
    except Exception as e:
        logger.error(f"Error loading usage data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=Config.AUTO_REFRESH_SECONDS)
def load_cost_stats():
    """Load cost statistics with caching."""
    db = init_database()
    try:
        return db.get_cost_stats_7d()
    except Exception as e:
        logger.error(f"Error loading cost stats: {e}")
        return {}

@st.cache_data(ttl=Config.AUTO_REFRESH_SECONDS)
def load_combined_price_data():
    """Load combined historical and forecast price data with caching."""
    db = init_database()
    try:
        return db.get_combined_historical_and_forecast_data()
    except Exception as e:
        logger.error(f"Error loading combined price data: {e}")
        return {'historical': pd.DataFrame(), 'forecast': pd.DataFrame()}

@st.cache_data(ttl=Config.AUTO_REFRESH_SECONDS)
def get_last_updated():
    """Get last updated timestamp."""
    db = init_database()
    try:
        return db.get_latest_data_timestamp()
    except Exception as e:
        logger.error(f"Error getting last updated: {e}")
        return None

def main():
    """Main application function."""
    
    # Header
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title(Config.APP_TITLE)
        st.markdown("*Real-time energy monitoring and cost analysis*")
    
    with col2:
        # Auto-refresh button
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
        
        # Last updated timestamp
        last_updated = get_last_updated()
        if last_updated:
            st.markdown(f'<div class="last-updated">Last updated: {last_updated.strftime("%Y-%m-%d %H:%M AEST")}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Load data
    try:
        price_data = load_price_data()
        combined_price_data = load_combined_price_data()
        usage_data = load_usage_data()
        cost_stats = load_cost_stats()
        
        # Check for data availability
        historical_df = combined_price_data.get('historical', pd.DataFrame())
        if historical_df.empty and usage_data.empty:
            st.error("❌ No data available. Please check that the data collector service is running and has collected data.")
            st.info("💡 Run the data collector service: `cd backend/datacollector-service && python main.py`")
            return
        
        # Price Section
        st.markdown("## 💰 Electricity Prices")
        
        # Show forecast toggle
        show_forecasts = st.checkbox("Show 10-hour forecasts", value=True, help="Display price forecasts with uncertainty bands")
        
        if show_forecasts and not combined_price_data['historical'].empty:
            # Combined historical + forecast chart
            if not combined_price_data['forecast'].empty:
                st.info("📈 Showing historical prices + 10-hour forecasts with uncertainty bands")
            else:
                st.warning("⚠️ No forecast data available - showing historical data only")
            
            # Price summary metrics (using historical data)
            display_price_summary(combined_price_data['historical'])
            
            # Combined price chart with forecasts
            combined_chart = create_price_chart_with_forecasts(combined_price_data)
            st.plotly_chart(combined_chart, use_container_width=True)
            
        elif not price_data.empty:
            # Historical only chart
            st.info("📊 Showing historical prices only")
            
            # Price summary metrics
            display_price_summary(price_data)
            
            # Historical price chart
            price_chart = create_price_chart(price_data)
            st.plotly_chart(price_chart, use_container_width=True)
        else:
            st.warning("No price data available for the past 24 hours")
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        # Usage Section
        st.markdown("## ⚡ Energy Usage")
        
        if not usage_data.empty:
            # Usage summary metrics
            display_usage_summary(usage_data)
            
            # Usage chart
            usage_chart = create_usage_chart(usage_data)
            st.plotly_chart(usage_chart, use_container_width=True)
        else:
            st.warning("No usage data available for the past 24 hours")
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        # Cost Statistics Section
        if cost_stats and cost_stats.get('days_with_data', 0) > 0:
            display_cost_stats(cost_stats)
            
            # Daily breakdown charts
            col1, col2 = st.columns(2)
            
            with col1:
                cost_chart = create_daily_cost_chart(cost_stats)
                st.plotly_chart(cost_chart, use_container_width=True)
            
            with col2:
                usage_breakdown_chart = create_usage_breakdown_chart(cost_stats)
                st.plotly_chart(usage_breakdown_chart, use_container_width=True)
        else:
            st.warning("No cost statistics available for the past 7 days")
        
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        logger.error(f"Application error: {e}")
        st.info("Please check the database connection and ensure the data collector service is running.")


if __name__ == "__main__":
    main()
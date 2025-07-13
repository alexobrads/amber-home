"""
Streamlit dashboard for Amber Electric usage and pricing data.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from amber_client import AmberClient


# Page configuration
st.set_page_config(
    page_title="Amber Electric Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("⚡ Amber Electric Dashboard")

# Initialize session state
if 'amber_client' not in st.session_state:
    st.session_state.amber_client = None
if 'sites' not in st.session_state:
    st.session_state.sites = None
if 'selected_site_id' not in st.session_state:
    st.session_state.selected_site_id = None


def initialize_client():
    """Initialize the Amber API client."""
    try:
        client = AmberClient()
        st.session_state.amber_client = client
        st.session_state.sites = client.get_sites()
        return True
    except Exception as e:
        st.error(f"Failed to initialize Amber client: {str(e)}")
        st.info("Make sure your AMBER_API_KEY environment variable is set correctly.")
        return False


def display_price_descriptor(descriptor):
    """Display price descriptor with appropriate color."""
    color_map = {
        'extremelyLow': '🟢',
        'veryLow': '🟢',
        'low': '🟡',
        'neutral': '🟠',
        'high': '🔴',
        'spike': '🚨'
    }
    return f"{color_map.get(descriptor, '⚪')} {descriptor.title()}"


def display_spike_status(spike_status):
    """Display spike status with appropriate warning."""
    if spike_status == 'spike':
        return "🚨 SPIKE ACTIVE"
    elif spike_status == 'potential':
        return "⚠️ Potential Spike"
    else:
        return "✅ Normal"


def create_price_chart(price_data):
    """Create a price trend chart."""
    df = pd.DataFrame([
        {
            'time': getattr(interval, 'nem_time', None),
            'price': getattr(interval, 'per_kwh', 0),
            'spot_price': getattr(interval, 'spot_per_kwh', 0),
            'descriptor': getattr(interval, 'descriptor', 'unknown'),
            'type': getattr(interval, 'type', 'unknown'),
            'renewables': getattr(interval, 'renewables', 0)
        }
        for interval in price_data
    ])
    
    df['time'] = pd.to_datetime(df['time'])
    
    # Create the main price chart
    fig = go.Figure()
    
    # Add price line
    fig.add_trace(go.Scatter(
        x=df['time'],
        y=df['price'],
        mode='lines+markers',
        name='Your Price (c/kWh)',
        line=dict(color='blue', width=2),
        hovertemplate='%{x}<br>Price: %{y:.2f} c/kWh<extra></extra>'
    ))
    
    # Add spot price line
    fig.add_trace(go.Scatter(
        x=df['time'],
        y=df['spot_price'],
        mode='lines',
        name='Spot Price (c/kWh)',
        line=dict(color='orange', width=1, dash='dash'),
        hovertemplate='%{x}<br>Spot Price: %{y:.2f} c/kWh<extra></extra>'
    ))
    
    # Color code based on price descriptor
    spike_data = df[df['descriptor'] == 'spike']
    if not spike_data.empty:
        fig.add_trace(go.Scatter(
            x=spike_data['time'],
            y=spike_data['price'],
            mode='markers',
            name='Price Spikes',
            marker=dict(color='red', size=8, symbol='triangle-up'),
            hovertemplate='%{x}<br>SPIKE: %{y:.2f} c/kWh<extra></extra>'
        ))
    
    fig.update_layout(
        title="Electricity Price Trends",
        xaxis_title="Time",
        yaxis_title="Price (c/kWh)",
        hovermode='x unified',
        height=400
    )
    
    return fig


def create_usage_chart(usage_data):
    """Create a usage chart showing consumption and generation."""
    df = pd.DataFrame([
        {
            'time': getattr(usage, 'nem_time', None),
            'kwh': getattr(usage, 'kwh', 0),
            'cost': getattr(usage, 'cost', 0) / 100,  # Convert cents to dollars
            'channel': getattr(usage, 'channel_identifier', getattr(usage, 'channelIdentifier', 'unknown')),
            'channel_type': getattr(usage, 'channel_type', getattr(usage, 'channelType', 'unknown')),
            'quality': getattr(usage, 'quality', 'unknown')
        }
        for usage in usage_data
    ])
    
    df['time'] = pd.to_datetime(df['time'])
    
    # Separate consumption and generation
    consumption = df[df['kwh'] >= 0]
    generation = df[df['kwh'] < 0]
    
    fig = go.Figure()
    
    if not consumption.empty:
        fig.add_trace(go.Bar(
            x=consumption['time'],
            y=consumption['kwh'],
            name='Consumption',
            marker_color='red',
            hovertemplate='%{x}<br>Consumption: %{y:.2f} kWh<br>Cost: $%{customdata:.2f}<extra></extra>',
            customdata=consumption['cost']
        ))
    
    if not generation.empty:
        fig.add_trace(go.Bar(
            x=generation['time'],
            y=generation['kwh'].abs(),
            name='Solar Generation',
            marker_color='green',
            hovertemplate='%{x}<br>Generation: %{y:.2f} kWh<br>Credit: $%{customdata:.2f}<extra></extra>',
            customdata=generation['cost'].abs()
        ))
    
    fig.update_layout(
        title="Energy Usage and Generation",
        xaxis_title="Time",
        yaxis_title="Energy (kWh)",
        barmode='group',
        height=400
    )
    
    return fig


def main():
    """Main dashboard function."""
    
    # Initialize client if needed
    if st.session_state.amber_client is None:
        if not initialize_client():
            st.stop()
    
    # Sidebar for site selection
    with st.sidebar:
        st.header("Site Selection")
        
        if st.session_state.sites:
            site_options = {
                f"{site.id} ({site.nmi})": site.id 
                for site in st.session_state.sites 
                if hasattr(site, 'status') and site.status == 'active' or not hasattr(site, 'status')
            }
            
            # Debug button
            if st.button("🔍 Debug API Objects"):
                try:
                    if st.session_state.selected_site_id:
                        prices = st.session_state.amber_client.get_current_prices(st.session_state.selected_site_id, next_hours=1)
                        if prices:
                            st.write("**Price object attributes:**")
                            st.json({attr: str(getattr(prices[0], attr, 'N/A')) for attr in dir(prices[0]) if not attr.startswith('_')})
                except Exception as e:
                    st.error(f"Debug error: {e}")
            
            if site_options:
                selected_site_name = st.selectbox(
                    "Choose your site:",
                    options=list(site_options.keys()),
                    key="site_selector"
                )
                st.session_state.selected_site_id = site_options[selected_site_name]
                
                # Display site info
                selected_site = next(
                    site for site in st.session_state.sites 
                    if site.id == st.session_state.selected_site_id
                )
                if hasattr(selected_site, 'network'):
                    st.info(f"**Network:** {selected_site.network}")
                if hasattr(selected_site, 'channels'):
                    st.info(f"**Channels:** {len(selected_site.channels)}")
                st.info(f"**Site ID:** {selected_site.id}")
                st.info(f"**NMI:** {selected_site.nmi}")
            else:
                st.error("No active sites found")
                st.stop()
        else:
            st.error("No sites available")
            st.stop()
    
    # Main dashboard content
    if st.session_state.selected_site_id:
        
        # Current prices section
        st.header("🔔 Current Prices")
        
        try:
            current_prices = st.session_state.amber_client.get_current_prices(
                st.session_state.selected_site_id, 
                next_hours=24
            )
            
            if current_prices:
                # Current interval (first in the list)
                current = current_prices[0]
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Current Price",
                        f"{current.per_kwh:.2f} c/kWh",
                        help="Your current electricity price including all fees"
                    )
                
                with col2:
                    st.metric(
                        "Spot Price", 
                        f"{current.spot_per_kwh:.2f} c/kWh",
                        help="Wholesale market price"
                    )
                
                with col3:
                    st.write("**Price Level**")
                    if hasattr(current, 'descriptor'):
                        st.write(display_price_descriptor(current.descriptor))
                    else:
                        st.write("N/A")
                
                with col4:
                    st.write("**Spike Status**")
                    if hasattr(current, 'spike_status'):
                        st.write(display_spike_status(current.spike_status))
                    else:
                        st.write("N/A")
                
                # Price trend chart
                st.plotly_chart(create_price_chart(current_prices), use_container_width=True)
                
            else:
                st.warning("No current price data available")
                
        except Exception as e:
            st.error(f"Failed to load current prices: {str(e)}")
        
        # Usage data section
        st.header("📊 Recent Usage")
        
        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime.now().date() - timedelta(days=7),
                max_value=datetime.now().date()
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=datetime.now().date(),
                max_value=datetime.now().date()
            )
        
        if start_date <= end_date:
            try:
                usage_data = st.session_state.amber_client.get_usage_data(
                    st.session_state.selected_site_id,
                    datetime.combine(start_date, datetime.min.time()),
                    datetime.combine(end_date, datetime.min.time())
                )
                
                if usage_data:
                    # Usage summary with better cost calculation
                    total_consumption = sum(getattr(u, 'kwh', 0) for u in usage_data if getattr(u, 'kwh', 0) > 0)
                    total_generation = abs(sum(getattr(u, 'kwh', 0) for u in usage_data if getattr(u, 'kwh', 0) < 0))
                    
                    # Separate consumption costs and generation credits (convert from cents to dollars)
                    consumption_cost = sum(getattr(u, 'cost', 0) for u in usage_data if getattr(u, 'cost', 0) > 0) / 100
                    generation_credit = abs(sum(getattr(u, 'cost', 0) for u in usage_data if getattr(u, 'cost', 0) < 0)) / 100
                    net_cost = consumption_cost - generation_credit
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Consumption", f"{total_consumption:.2f} kWh")
                    with col2:
                        st.metric("Total Generation", f"{total_generation:.2f} kWh")
                    with col3:
                        st.metric("Consumption Cost", f"${consumption_cost:.2f}")
                    with col4:
                        st.metric("Net Cost", f"${net_cost:.2f}", help="Consumption cost minus generation credits")
                    
                    # Show breakdown
                    if generation_credit > 0:
                        st.info(f"💰 Generation Credits: ${generation_credit:.2f}")
                    
                    # Debug cost data
                    with st.expander("🔍 Cost Breakdown Details"):
                        cost_df = pd.DataFrame([
                            {
                                'time': getattr(u, 'nem_time', 'Unknown'),
                                'kwh': getattr(u, 'kwh', 0),
                                'cost_cents': getattr(u, 'cost', 0),
                                'cost_dollars': getattr(u, 'cost', 0) / 100,
                                'channel': getattr(u, 'channel_identifier', getattr(u, 'channelIdentifier', 'Unknown')),
                                'quality': getattr(u, 'quality', 'Unknown')
                            }
                            for u in usage_data[:10]  # Show first 10 entries
                        ])
                        st.dataframe(cost_df)
                    
                    # Usage chart
                    st.plotly_chart(create_usage_chart(usage_data), use_container_width=True)
                    
                else:
                    st.warning("No usage data available for the selected date range")
                    
            except Exception as e:
                st.error(f"Failed to load usage data: {str(e)}")
        else:
            st.error("Start date must be before end date")
        
        # Renewable energy section
        st.header("🌱 Renewable Energy")
        
        try:
            # Determine state from site network (simplified mapping)
            state_mapping = {
                'jemena': 'vic',
                'ausgrid': 'nsw',
                'energex': 'qld',
                'sa power networks': 'sa'
            }
            
            selected_site = next(
                site for site in st.session_state.sites 
                if site.id == st.session_state.selected_site_id
            )
            
            state = 'vic'  # Default to Victoria
            if hasattr(selected_site, 'network') and selected_site.network:
                for network, state_code in state_mapping.items():
                    if network.lower() in selected_site.network.lower():
                        state = state_code
                        break
            
            renewable_data = st.session_state.amber_client.get_renewable_data(state, next_hours=12, previous_hours=12)
            
            if renewable_data:
                # Find current interval (the one closest to now or marked as current)
                current_renewable = None
                for item in renewable_data:
                    if isinstance(item, dict) and item.get('type') == 'CurrentRenewable':
                        current_renewable = item
                        break
                
                if not current_renewable and renewable_data:
                    # Fallback to middle item if no current type found
                    current_renewable = renewable_data[len(renewable_data)//2]
                
                if current_renewable:
                    renewables_pct = current_renewable.get('renewables', 0)
                    descriptor = current_renewable.get('descriptor', 'unknown')
                    
                    st.metric(
                        f"Current Renewables ({state.upper()})",
                        f"{renewables_pct:.1f}%",
                        help="Percentage of renewable energy in the grid right now"
                    )
                    
                    # Show descriptor
                    descriptor_map = {
                        'best': '🌟 Best',
                        'great': '💚 Great', 
                        'ok': '🟡 OK',
                        'notGreat': '🟠 Not Great',
                        'worst': '🔴 Worst'
                    }
                    st.write(f"**Grid Status**: {descriptor_map.get(descriptor, descriptor.title())}")
                
                # Renewable trend chart
                df = pd.DataFrame([
                    {
                        'time': item.get('nemTime'),
                        'renewables': item.get('renewables', 0),
                        'descriptor': item.get('descriptor', 'unknown'),
                        'type': item.get('type', 'unknown')
                    }
                    for item in renewable_data
                    if isinstance(item, dict)
                ])
                
                if not df.empty:
                    df['time'] = pd.to_datetime(df['time'])
                    
                    fig = px.line(
                        df, 
                        x='time', 
                        y='renewables',
                        title="Renewable Energy Percentage",
                        labels={'renewables': 'Renewables (%)', 'time': 'Time'},
                        hover_data=['descriptor', 'type']
                    )
                    fig.update_traces(line_color='green')
                    fig.update_layout(height=300)
                    
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Renewable energy data is not available.")
                
        except Exception as e:
            st.error(f"Failed to load renewable data: {str(e)}")


if __name__ == "__main__":
    main()
"""
Price chart components for the frontend.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
import pytz


def create_price_chart(df: pd.DataFrame) -> go.Figure:
    """Create price chart for import and export."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No price data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        return fig
    
    # Separate import and export data
    import_data = df[df['channel_type'].str.contains('GENERAL', na=False)]
    export_data = df[df['channel_type'].str.contains('FEEDIN', na=False)]
    
    fig = go.Figure()
    
    # Add import prices
    if not import_data.empty:
        fig.add_trace(go.Scatter(
            x=import_data['aest_time'],
            y=import_data['per_kwh'],
            mode='lines+markers',
            name='Import Price (E1)',
            line=dict(color='#ff6b6b', width=2),
            marker=dict(size=4),
            hovertemplate='<b>Import Price</b><br>' +
                         'Time: %{x}<br>' +
                         'Price: %{y:.2f}¢/kWh<br>' +
                         '<extra></extra>'
        ))
    
    # Add export prices
    if not export_data.empty:
        fig.add_trace(go.Scatter(
            x=export_data['aest_time'],
            y=export_data['per_kwh'],
            mode='lines+markers',
            name='Export Price (B1)',
            line=dict(color='#4ecdc4', width=2),
            marker=dict(size=4),
            hovertemplate='<b>Export Price</b><br>' +
                         'Time: %{x}<br>' +
                         'Price: %{y:.2f}¢/kWh<br>' +
                         '<extra></extra>'
        ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text='Electricity Prices - Past 24 Hours',
            font=dict(size=20, color='#2c3e50')
        ),
        xaxis_title='Time (AEST)',
        yaxis_title='Price (¢/kWh)',
        hovermode='x unified',
        template='plotly_white',
        height=400,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Format x-axis with date and time
    fig.update_xaxes(
        tickformat='%m/%d<br>%H:%M',  # Date on top line, time on bottom
        dtick=3600000 * 2,  # 2 hour intervals
        tickangle=45
    )
    
    return fig


def display_price_summary(df: pd.DataFrame):
    """Display price summary statistics."""
    if df.empty:
        st.warning("No price data available for summary")
        return
    
    # Calculate summary stats - get most recent (last) values since data is now ordered ASC
    current_import = df[df['channel_type'].str.contains('GENERAL', na=False)]['per_kwh'].iloc[-1] if not df[df['channel_type'].str.contains('GENERAL', na=False)].empty else 0
    current_export = df[df['channel_type'].str.contains('FEEDIN', na=False)]['per_kwh'].iloc[-1] if not df[df['channel_type'].str.contains('FEEDIN', na=False)].empty else 0
    
    avg_import = df[df['channel_type'].str.contains('GENERAL', na=False)]['per_kwh'].mean()
    avg_export = df[df['channel_type'].str.contains('FEEDIN', na=False)]['per_kwh'].mean()
    
    max_import = df[df['channel_type'].str.contains('GENERAL', na=False)]['per_kwh'].max()
    min_import = df[df['channel_type'].str.contains('GENERAL', na=False)]['per_kwh'].min()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Current Import Price",
            value=f"{current_import:.2f}¢/kWh",
            delta=f"{current_import - avg_import:.2f}¢" if not pd.isna(avg_import) else None
        )
    
    with col2:
        st.metric(
            label="Current Export Price",
            value=f"{current_export:.2f}¢/kWh",
            delta=f"{current_export - avg_export:.2f}¢" if not pd.isna(avg_export) else None
        )
    
    with col3:
        st.metric(
            label="24h Max Import",
            value=f"{max_import:.2f}¢/kWh" if not pd.isna(max_import) else "N/A"
        )
    
    with col4:
        st.metric(
            label="24h Min Import",
            value=f"{min_import:.2f}¢/kWh" if not pd.isna(min_import) else "N/A"
        )
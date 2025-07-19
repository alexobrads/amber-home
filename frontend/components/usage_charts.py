"""
Usage chart components for the frontend.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
import pytz


def create_usage_chart(df: pd.DataFrame) -> go.Figure:
    """Create usage chart for import and export."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No usage data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        return fig
    
    # Separate import and export data
    import_data = df[df['kwh'] > 0].copy()
    export_data = df[df['kwh'] < 0].copy()
    
    # Convert export to positive values for display
    export_data['kwh_display'] = export_data['kwh'].abs()
    
    fig = go.Figure()
    
    # Add import usage (positive values)
    if not import_data.empty:
        fig.add_trace(go.Scatter(
            x=import_data['aest_time'],
            y=import_data['kwh'],
            mode='lines',
            name='Import Usage (E1)',
            line=dict(color='#ff6b6b', width=2),
            fill='tozeroy',
            fillcolor='rgba(255, 107, 107, 0.3)',
            hovertemplate='<b>Import Usage</b><br>' +
                         'Time: %{x}<br>' +
                         'Usage: %{y:.3f} kWh<br>' +
                         '<extra></extra>'
        ))
    
    # Add export usage (shown as negative for visual distinction)
    if not export_data.empty:
        fig.add_trace(go.Scatter(
            x=export_data['aest_time'],
            y=export_data['kwh'],  # Keep negative for visual distinction
            mode='lines',
            name='Export Usage (B1)',
            line=dict(color='#4ecdc4', width=2),
            fill='tozeroy',
            fillcolor='rgba(78, 205, 196, 0.3)',
            hovertemplate='<b>Export Usage</b><br>' +
                         'Time: %{x}<br>' +
                         'Usage: %{y:.3f} kWh<br>' +
                         '<extra></extra>'
        ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text='Energy Usage - Past 24 Hours',
            font=dict(size=20, color='#2c3e50')
        ),
        xaxis_title='Time (AEST)',
        yaxis_title='Usage (kWh)',
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
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    return fig


def display_usage_summary(df: pd.DataFrame):
    """Display usage summary statistics."""
    if df.empty:
        st.warning("No usage data available for summary")
        return
    
    # Calculate summary stats
    total_import = df[df['kwh'] > 0]['kwh'].sum()
    total_export = df[df['kwh'] < 0]['kwh'].abs().sum()
    net_usage = df['kwh'].sum()
    
    avg_import = df[df['kwh'] > 0]['kwh'].mean()
    avg_export = df[df['kwh'] < 0]['kwh'].abs().mean()
    
    # Calculate cost
    total_cost = df['cost'].sum() / 100  # Convert cents to dollars
    import_cost = df[df['cost'] > 0]['cost'].sum() / 100
    export_credit = df[df['cost'] < 0]['cost'].abs().sum() / 100
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Import",
            value=f"{total_import:.2f} kWh",
            delta=f"${import_cost:.2f} cost" if import_cost > 0 else None
        )
    
    with col2:
        st.metric(
            label="Total Export",
            value=f"{total_export:.2f} kWh",
            delta=f"${export_credit:.2f} credit" if export_credit > 0 else None
        )
    
    with col3:
        st.metric(
            label="Net Usage",
            value=f"{net_usage:.2f} kWh",
            delta="Import - Export"
        )
    
    with col4:
        st.metric(
            label="Net Cost (24h)",
            value=f"${total_cost:.2f}",
            delta="Import - Export"
        )
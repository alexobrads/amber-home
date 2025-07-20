"""
Price chart components for the frontend.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
import pytz
from typing import Dict


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


def create_price_chart_with_forecasts(data: Dict[str, pd.DataFrame]) -> go.Figure:
    """Create price chart showing historical data + 10h forecasts with uncertainty bands."""
    historical_df = data.get('historical', pd.DataFrame())
    forecast_df = data.get('forecast', pd.DataFrame())
    
    fig = go.Figure()
    
    # If no data available
    if historical_df.empty and forecast_df.empty:
        fig.add_annotation(
            text="No price data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        return fig
    
    # Process historical data
    if not historical_df.empty:
        # Historical import prices
        hist_import = historical_df[historical_df['channel_type'].str.contains('GENERAL', na=False)]
        if not hist_import.empty:
            fig.add_trace(go.Scatter(
                x=hist_import['aest_time'],
                y=hist_import['per_kwh'],
                mode='lines+markers',
                name='Historical Import',
                line=dict(color='#ff6b6b', width=2),
                marker=dict(size=4),
                hovertemplate='<b>Historical Import</b><br>' +
                             'Time: %{x}<br>' +
                             'Price: %{y:.2f}¢/kWh<br>' +
                             '<extra></extra>'
            ))
        
        # Historical export prices
        hist_export = historical_df[historical_df['channel_type'].str.contains('FEEDIN', na=False)]
        if not hist_export.empty:
            fig.add_trace(go.Scatter(
                x=hist_export['aest_time'],
                y=hist_export['per_kwh'],
                mode='lines+markers',
                name='Historical Export',
                line=dict(color='#4ecdc4', width=2),
                marker=dict(size=4),
                hovertemplate='<b>Historical Export</b><br>' +
                             'Time: %{x}<br>' +
                             'Price: %{y:.2f}¢/kWh<br>' +
                             '<extra></extra>'
            ))
    
    # Process forecast data
    if not forecast_df.empty:
        # Forecast import prices with uncertainty
        forecast_import = forecast_df[forecast_df['channel_type'].str.contains('GENERAL', na=False)]
        if not forecast_import.empty:
            # Main forecast line (predicted price)
            fig.add_trace(go.Scatter(
                x=forecast_import['aest_time'],
                y=forecast_import['per_kwh'],
                mode='lines',
                name='Forecast Import',
                line=dict(color='#ff6b6b', width=2, dash='dash'),
                hovertemplate='<b>Forecast Import</b><br>' +
                             'Time: %{x}<br>' +
                             'Price: %{y:.2f}¢/kWh<br>' +
                             '<extra></extra>'
            ))
            
            # Add uncertainty bands if available
            if 'advanced_price_low' in forecast_import.columns and 'advanced_price_high' in forecast_import.columns:
                # High uncertainty bound
                fig.add_trace(go.Scatter(
                    x=forecast_import['aest_time'],
                    y=forecast_import['advanced_price_high'],
                    mode='lines',
                    name='Import High',
                    line=dict(color='rgba(255, 107, 107, 0)', width=0),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
                # Low uncertainty bound with fill
                fig.add_trace(go.Scatter(
                    x=forecast_import['aest_time'],
                    y=forecast_import['advanced_price_low'],
                    mode='lines',
                    name='Import Uncertainty',
                    line=dict(color='rgba(255, 107, 107, 0)', width=0),
                    fill='tonexty',
                    fillcolor='rgba(255, 107, 107, 0.2)',
                    hovertemplate='<b>Import Uncertainty</b><br>' +
                                 'Time: %{x}<br>' +
                                 'Low: %{y:.2f}¢/kWh<br>' +
                                 '<extra></extra>'
                ))
        
        # Forecast export prices with uncertainty
        forecast_export = forecast_df[forecast_df['channel_type'].str.contains('FEEDIN', na=False)]
        if not forecast_export.empty:
            # Main forecast line
            fig.add_trace(go.Scatter(
                x=forecast_export['aest_time'],
                y=forecast_export['per_kwh'],
                mode='lines',
                name='Forecast Export',
                line=dict(color='#4ecdc4', width=2, dash='dash'),
                hovertemplate='<b>Forecast Export</b><br>' +
                             'Time: %{x}<br>' +
                             'Price: %{y:.2f}¢/kWh<br>' +
                             '<extra></extra>'
            ))
            
            # Add uncertainty bands if available
            if 'advanced_price_low' in forecast_export.columns and 'advanced_price_high' in forecast_export.columns:
                # High uncertainty bound
                fig.add_trace(go.Scatter(
                    x=forecast_export['aest_time'],
                    y=forecast_export['advanced_price_high'],
                    mode='lines',
                    name='Export High',
                    line=dict(color='rgba(78, 205, 196, 0)', width=0),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
                # Low uncertainty bound with fill
                fig.add_trace(go.Scatter(
                    x=forecast_export['aest_time'],
                    y=forecast_export['advanced_price_low'],
                    mode='lines',
                    name='Export Uncertainty',
                    line=dict(color='rgba(78, 205, 196, 0)', width=0),
                    fill='tonexty',
                    fillcolor='rgba(78, 205, 196, 0.2)',
                    hovertemplate='<b>Export Uncertainty</b><br>' +
                                 'Time: %{x}<br>' +
                                 'Low: %{y:.2f}¢/kWh<br>' +
                                 '<extra></extra>'
                ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text='Electricity Prices - Historical + 10h Forecasts',
            font=dict(size=20, color='#2c3e50')
        ),
        xaxis_title='Time (AEST)',
        yaxis_title='Price (¢/kWh)',
        hovermode='x unified',
        template='plotly_white',
        height=500,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Add vertical line to separate historical from forecast
    if not historical_df.empty and not forecast_df.empty:
        last_historical_time = historical_df['aest_time'].max()
        fig.add_shape(
            type="line",
            x0=last_historical_time,
            x1=last_historical_time,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(dash="dot", color="gray", width=2)
        )
        fig.add_annotation(
            x=last_historical_time,
            y=1,
            yref="paper",
            text="Forecast starts",
            showarrow=False,
            yanchor="bottom",
            xanchor="left",
            bgcolor="rgba(255,255,255,0.8)"
        )
    
    # Format x-axis
    fig.update_xaxes(
        tickformat='%H:%M',
        dtick=3600000 * 2,  # 2 hour intervals
        tickangle=45
    )
    
    return fig
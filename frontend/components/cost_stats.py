"""
Cost statistics components for the frontend.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
from typing import Dict, Any


def display_cost_stats(stats: Dict[str, Any]):
    """Display cost statistics for the past week."""
    if not stats or stats['days_with_data'] == 0:
        st.warning("No cost data available for the past week")
        return
    
    st.subheader("📊 Cost Statistics - Past 7 Days")
    
    # Main metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Cost",
            value=f"${stats['total_cost']:.2f}",
            help="Net cost (import - export) for the past 7 days"
        )
    
    with col2:
        st.metric(
            label="Average Daily Cost",
            value=f"${stats['avg_daily_cost']:.2f}",
            help="Average daily net cost"
        )
    
    with col3:
        st.metric(
            label="Total Import Cost",
            value=f"${stats['total_import_cost']:.2f}",
            help="Total cost for electricity consumed"
        )
    
    with col4:
        st.metric(
            label="Total Export Credit",
            value=f"${stats['total_export_cost']:.2f}",
            help="Total credit for electricity exported"
        )
    
    # Energy usage metrics
    st.subheader("⚡ Energy Usage - Past 7 Days")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Import",
            value=f"{stats['total_kwh_import']:.1f} kWh",
            help="Total electricity consumed"
        )
    
    with col2:
        st.metric(
            label="Total Export",
            value=f"{stats['total_kwh_export']:.1f} kWh",
            help="Total electricity exported (solar generation)"
        )
    
    with col3:
        net_kwh = stats['total_kwh_import'] - stats['total_kwh_export']
        st.metric(
            label="Net Usage",
            value=f"{net_kwh:.1f} kWh",
            help="Net electricity consumed (import - export)"
        )
    
    with col4:
        if stats['total_kwh_import'] > 0:
            avg_cost_per_kwh = stats['total_import_cost'] / stats['total_kwh_import']
            st.metric(
                label="Avg Cost/kWh",
                value=f"${avg_cost_per_kwh:.3f}",
                help="Average cost per kWh imported"
            )
        else:
            st.metric(
                label="Avg Cost/kWh",
                value="N/A",
                help="No import data available"
            )


def create_daily_cost_chart(stats: Dict[str, Any]) -> go.Figure:
    """Create daily cost breakdown chart."""
    if not stats or 'daily_data' not in stats or stats['daily_data'].empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No daily cost data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        return fig
    
    df = stats['daily_data']
    
    fig = go.Figure()
    
    # Add import costs
    fig.add_trace(go.Bar(
        x=df['date'],
        y=df['daily_cost_import'],
        name='Import Cost',
        marker_color='#ff6b6b',
        hovertemplate='<b>Import Cost</b><br>' +
                     'Date: %{x}<br>' +
                     'Cost: $%{y:.2f}<br>' +
                     '<extra></extra>'
    ))
    
    # Add export credits (negative values)
    fig.add_trace(go.Bar(
        x=df['date'],
        y=-df['daily_cost_export'],  # Negative for visual distinction
        name='Export Credit',
        marker_color='#4ecdc4',
        hovertemplate='<b>Export Credit</b><br>' +
                     'Date: %{x}<br>' +
                     'Credit: $%{y:.2f}<br>' +
                     '<extra></extra>'
    ))
    
    # Add net cost line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['daily_cost_net'],
        mode='lines+markers',
        name='Net Cost',
        line=dict(color='#2c3e50', width=3),
        marker=dict(size=8),
        hovertemplate='<b>Net Cost</b><br>' +
                     'Date: %{x}<br>' +
                     'Net: $%{y:.2f}<br>' +
                     '<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text='Daily Cost Breakdown - Past 7 Days',
            font=dict(size=20, color='#2c3e50')
        ),
        xaxis_title='Date',
        yaxis_title='Cost ($)',
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
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    return fig


def create_usage_breakdown_chart(stats: Dict[str, Any]) -> go.Figure:
    """Create usage breakdown chart."""
    if not stats or 'daily_data' not in stats or stats['daily_data'].empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No daily usage data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        return fig
    
    df = stats['daily_data']
    
    fig = go.Figure()
    
    # Add import usage
    fig.add_trace(go.Bar(
        x=df['date'],
        y=df['daily_kwh_import'],
        name='Import (kWh)',
        marker_color='#ff6b6b',
        hovertemplate='<b>Import Usage</b><br>' +
                     'Date: %{x}<br>' +
                     'Usage: %{y:.1f} kWh<br>' +
                     '<extra></extra>'
    ))
    
    # Add export usage (negative values for visual distinction)
    fig.add_trace(go.Bar(
        x=df['date'],
        y=-df['daily_kwh_export'],  # Negative for visual distinction
        name='Export (kWh)',
        marker_color='#4ecdc4',
        hovertemplate='<b>Export Usage</b><br>' +
                     'Date: %{x}<br>' +
                     'Usage: %{y:.1f} kWh<br>' +
                     '<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text='Daily Usage Breakdown - Past 7 Days',
            font=dict(size=20, color='#2c3e50')
        ),
        xaxis_title='Date',
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
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    return fig
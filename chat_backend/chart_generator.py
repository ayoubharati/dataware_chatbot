import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, Any, Optional
import json

def generate_plotly_chart(df: pd.DataFrame, chart_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a complete Plotly chart specification from DataFrame
    Returns a dict that can be directly used by Plotly.js on frontend
    """
    if df.empty:
        return {
            "data": [],
            "layout": {
                "title": "No data available",
                "showlegend": False
            },
            "config": {"displayModeBar": False}
        }
    
    # Aggregate/sample data if too large
    df_processed = aggregate_or_sample_for_plotly(df, chart_type)
    
    try:
        if chart_type == "bar":
            return create_bar_chart(df_processed, config)
        elif chart_type == "line":
            return create_line_chart(df_processed, config)
        elif chart_type == "pie":
            return create_pie_chart(df_processed, config)
        elif chart_type == "scatter":
            return create_scatter_chart(df_processed, config)
        else:
            # Default to table or simple bar
            return create_bar_chart(df_processed, config)
            
    except Exception as e:
        # Fallback to simple table representation
        return create_fallback_chart(df_processed, str(e))

def aggregate_or_sample_for_plotly(df: pd.DataFrame, chart_type: str, max_points: int = 1000) -> pd.DataFrame:
    """Smart sampling/aggregation for Plotly charts"""
    if len(df) <= max_points:
        return df
    
    # More aggressive sampling since we're handling large datasets
    if chart_type == "bar":
        # For bar charts, group by categorical and sum numeric
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            aggregated = df.groupby(cat_col)[num_col].sum().reset_index()
            return aggregated.sort_values(num_col, ascending=False).head(50)
    
    elif chart_type == "line":
        # For time series, intelligent sampling
        date_cols = df.select_dtypes(include=['datetime64']).columns
        if len(date_cols) == 0:
            # Try to find date-like columns
            date_cols = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
        
        if len(date_cols) > 0:
            df_sorted = df.sort_values(date_cols[0])
            # Take every nth row to get approximately max_points
            step = max(1, len(df_sorted) // max_points)
            return df_sorted.iloc[::step]
    
    # Default: random sampling
    return df.sample(n=min(max_points, len(df)), random_state=42)

def create_bar_chart(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    """Create Plotly bar chart specification"""
    x_col = config.get('xKey') or df.columns[0]
    y_cols = config.get('yKeys', []) or [df.columns[1]] if len(df.columns) > 1 else [df.columns[0]]
    
    data = []
    for i, y_col in enumerate(y_cols[:3]):  # Limit to 3 series max
        data.append({
            "x": df[x_col].tolist(),
            "y": df[y_col].tolist(),
            "type": "bar",
            "name": y_col,
            "marker": {
                "color": f"rgba({54 + i * 40}, {162 + i * 25}, {235 - i * 20}, 0.8)"
            }
        })
    
    layout = {
        "title": config.get('title', 'Bar Chart'),
        "xaxis": {"title": x_col},
        "yaxis": {"title": "Value"},
        "showlegend": len(y_cols) > 1,
        "margin": {"t": 50, "b": 50, "l": 50, "r": 50}
    }
    
    return {
        "data": data,
        "layout": layout,
        "config": {"displayModeBar": True, "responsive": True}
    }

def create_line_chart(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    """Create Plotly line chart specification"""
    x_col = config.get('xKey') or df.columns[0]
    y_cols = config.get('yKeys', []) or [df.columns[1]] if len(df.columns) > 1 else [df.columns[0]]
    
    data = []
    for i, y_col in enumerate(y_cols[:3]):
        data.append({
            "x": df[x_col].tolist(),
            "y": df[y_col].tolist(),
            "type": "scatter",
            "mode": "lines+markers",
            "name": y_col,
            "line": {
                "color": f"rgba({54 + i * 40}, {162 + i * 25}, {235 - i * 20}, 1)",
                "width": 2
            }
        })
    
    layout = {
        "title": config.get('title', 'Line Chart'),
        "xaxis": {"title": x_col},
        "yaxis": {"title": "Value"},
        "showlegend": len(y_cols) > 1,
        "margin": {"t": 50, "b": 50, "l": 50, "r": 50}
    }
    
    return {
        "data": data,
        "layout": layout,
        "config": {"displayModeBar": True, "responsive": True}
    }

def create_pie_chart(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    """Create Plotly pie chart specification"""
    name_col = config.get('nameKey') or config.get('xKey') or df.columns[0]
    value_col = config.get('valueKey') or (config.get('yKeys', [{}])[0] if config.get('yKeys') else df.columns[1] if len(df.columns) > 1 else df.columns[0])
    
    # Take top 10 slices to avoid overcrowding
    df_top = df.nlargest(10, value_col) if value_col in df.columns else df.head(10)
    
    data = [{
        "type": "pie",
        "labels": df_top[name_col].tolist(),
        "values": df_top[value_col].tolist(),
        "textinfo": "label+percent",
        "hole": 0.3  # Makes it a donut chart
    }]
    
    layout = {
        "title": config.get('title', 'Pie Chart'),
        "margin": {"t": 50, "b": 50, "l": 50, "r": 50}
    }
    
    return {
        "data": data,
        "layout": layout,
        "config": {"displayModeBar": True, "responsive": True}
    }

def create_scatter_chart(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    """Create Plotly scatter chart specification"""
    x_col = config.get('xKey') or df.columns[0]
    y_col = config.get('yKey') or (config.get('yKeys', [{}])[0] if config.get('yKeys') else df.columns[1] if len(df.columns) > 1 else df.columns[0])
    
    data = [{
        "x": df[x_col].tolist(),
        "y": df[y_col].tolist(),
        "type": "scatter",
        "mode": "markers",
        "marker": {
            "color": "rgba(54, 162, 235, 0.8)",
            "size": 6
        },
        "name": f"{y_col} vs {x_col}"
    }]
    
    layout = {
        "title": config.get('title', 'Scatter Plot'),
        "xaxis": {"title": x_col},
        "yaxis": {"title": y_col},
        "margin": {"t": 50, "b": 50, "l": 50, "r": 50}
    }
    
    return {
        "data": data,
        "layout": layout,
        "config": {"displayModeBar": True, "responsive": True}
    }

def create_fallback_chart(df: pd.DataFrame, error_msg: str) -> Dict[str, Any]:
    """Fallback chart when generation fails"""
    return {
        "data": [],
        "layout": {
            "title": f"Chart generation failed: {error_msg}",
            "annotations": [{
                "text": f"Unable to generate chart. Data shape: {df.shape}",
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False
            }]
        },
        "config": {"displayModeBar": False}
    }
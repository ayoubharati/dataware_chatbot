import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, Any, Optional, List, Union
import json
import logging

logger = logging.getLogger(__name__)

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

def generate_chartjs_chart(df: pd.DataFrame, chart_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate Chart.js compatible chart specification
    Returns a dict that can be directly used by Chart.js on frontend
    """
    if df.empty:
        return {
            "type": "bar",
            "data": {
                "labels": [],
                "datasets": [{"data": [], "label": "No Data"}]
            },
            "options": {
                "title": {"display": True, "text": "No data available"},
                "responsive": True
            }
        }
    
    try:
        if chart_type == "bar":
            return create_chartjs_bar(df, config)
        elif chart_type == "line":
            return create_chartjs_line(df, config)
        elif chart_type == "pie":
            return create_chartjs_pie(df, config)
        elif chart_type == "scatter":
            return create_chartjs_scatter(df, config)
        else:
            # Default to bar chart
            return create_chartjs_bar(df, config)
            
    except Exception as e:
        logger.error(f"Chart.js generation failed: {e}")
        return create_chartjs_fallback(df, str(e))

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

def create_chartjs_bar(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    """Create Chart.js bar chart specification"""
    x_col = config.get('xKey') or df.columns[0]
    y_col = config.get('yKey') or (df.columns[1] if len(df.columns) > 1 else df.columns[0])
    
    labels = df[x_col].astype(str).tolist()
    data = df[y_col].tolist()
    
    return {
        "type": "bar",
        "data": {
            "labels": labels,
            "datasets": [{
                "label": y_col,
                "data": data,
                "backgroundColor": "rgba(54, 162, 235, 0.8)",
                "borderColor": "rgba(54, 162, 235, 1)",
                "borderWidth": 1
            }]
        },
        "options": {
            "title": {
                "display": True,
                "text": config.get('title', f'{y_col} by {x_col}')
            },
            "scales": {
                "x": {"title": {"display": True, "text": x_col}},
                "y": {"title": {"display": True, "text": y_col}}
            },
            "responsive": True,
            "maintainAspectRatio": False
        }
    }

def create_chartjs_line(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    """Create Chart.js line chart specification"""
    x_col = config.get('xKey') or df.columns[0]
    y_col = config.get('yKey') or (df.columns[1] if len(df.columns) > 1 else df.columns[0])
    
    labels = df[x_col].astype(str).tolist()
    data = df[y_col].tolist()
    
    return {
        "type": "line",
        "data": {
            "labels": labels,
            "datasets": [{
                "label": y_col,
                "data": data,
                "borderColor": "rgba(54, 162, 235, 1)",
                "backgroundColor": "rgba(54, 162, 235, 0.1)",
                "borderWidth": 2,
                "fill": True,
                "tension": 0.1
            }]
        },
        "options": {
            "title": {
                "display": True,
                "text": config.get('title', f'{y_col} over {x_col}')
            },
            "scales": {
                "x": {"title": {"display": True, "text": x_col}},
                "y": {"title": {"display": True, "text": y_col}}
            },
            "responsive": True,
            "maintainAspectRatio": False
        }
    }

def create_chartjs_pie(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    """Create Chart.js pie chart specification"""
    name_col = config.get('nameKey') or config.get('xKey') or df.columns[0]
    value_col = config.get('valueKey') or (df.columns[1] if len(df.columns) > 1 else df.columns[0])
    
    # Take top 8 slices to avoid overcrowding
    df_top = df.nlargest(8, value_col) if value_col in df.columns else df.head(8)
    
    labels = df_top[name_col].astype(str).tolist()
    data = df_top[value_col].tolist()
    
    # Generate colors
    colors = [
        "rgba(255, 99, 132, 0.8)", "rgba(54, 162, 235, 0.8)",
        "rgba(255, 206, 86, 0.8)", "rgba(75, 192, 192, 0.8)",
        "rgba(153, 102, 255, 0.8)", "rgba(255, 159, 64, 0.8)",
        "rgba(199, 199, 199, 0.8)", "rgba(83, 102, 255, 0.8)"
    ]
    
    return {
        "type": "pie",
        "data": {
            "labels": labels,
            "datasets": [{
                "data": data,
                "backgroundColor": colors[:len(data)],
                "borderColor": "white",
                "borderWidth": 2
            }]
        },
        "options": {
            "title": {
                "display": True,
                "text": config.get('title', f'{value_col} by {name_col}')
            },
            "responsive": True,
            "maintainAspectRatio": False
        }
    }

def create_chartjs_scatter(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    """Create Chart.js scatter chart specification"""
    x_col = config.get('xKey') or df.columns[0]
    y_col = config.get('yKey') or (df.columns[1] if len(df.columns) > 1 else df.columns[0])
    
    data = [{"x": float(x), "y": float(y)} for x, y in zip(df[x_col], df[y_col]) if pd.notna(x) and pd.notna(y)]
    
    return {
        "type": "scatter",
        "data": {
            "datasets": [{
                "label": f"{y_col} vs {x_col}",
                "data": data,
                "backgroundColor": "rgba(54, 162, 235, 0.8)",
                "borderColor": "rgba(54, 162, 235, 1)",
                "pointRadius": 6
            }]
        },
        "options": {
            "title": {
                "display": True,
                "text": config.get('title', f'{y_col} vs {x_col}')
            },
            "scales": {
                "x": {"title": {"display": True, "text": x_col}},
                "y": {"title": {"display": True, "text": y_col}}
            },
            "responsive": True,
            "maintainAspectRatio": False
        }
    }

def create_chartjs_fallback(df: pd.DataFrame, error_msg: str) -> Dict[str, Any]:
    """Fallback Chart.js chart when generation fails"""
    return {
        "type": "bar",
        "data": {
            "labels": ["Error"],
            "datasets": [{"data": [0], "label": "Chart generation failed"}]
        },
        "options": {
            "title": {
                "display": True,
                "text": f"Chart Error: {error_msg}"
            },
            "responsive": True
        }
    }

def determine_chart_type(df: pd.DataFrame, user_query: str) -> str:
    """
    Intelligently determine the best chart type based on data and user query
    """
    if df.empty:
        return "bar"
    
    # Analyze data structure
    num_cols = len(df.columns)
    num_rows = len(df)
    
    # Check for time series indicators
    time_indicators = ['date', 'time', 'year', 'month', 'day', 'hour']
    has_time = any(any(indicator in col.lower() for indicator in time_indicators) for col in df.columns)
    
    # Check for categorical vs numerical data
    categorical_cols = df.select_dtypes(include=['object', 'category', 'string']).columns
    numerical_cols = df.select_dtypes(include=['number']).columns
    
    # Analyze user query for chart preferences
    query_lower = user_query.lower()
    
    if 'line' in query_lower or 'trend' in query_lower or 'over time' in query_lower:
        return "line"
    elif 'pie' in query_lower or 'percentage' in query_lower or 'proportion' in query_lower:
        return "pie"
    elif 'scatter' in query_lower or 'correlation' in query_lower:
        return "scatter"
    elif 'bar' in query_lower or 'chart' in query_lower:
        return "bar"
    
    # Default logic based on data structure
    if has_time and len(numerical_cols) >= 1:
        return "line"  # Time series
    elif len(categorical_cols) >= 1 and len(numerical_cols) >= 1:
        if num_rows <= 10:
            return "pie"  # Small categorical data
        else:
            return "bar"  # Larger categorical data
    elif len(numerical_cols) >= 2:
        return "scatter"  # Two numerical columns
    else:
        return "bar"  # Default fallback

def is_chartable_data(df: pd.DataFrame, user_query: str) -> bool:
    """
    Determine if the data is suitable for charting
    """
    if df.empty:
        return False
    
    # Check if we have enough data
    if len(df) < 2:
        return False
    
    # Check if we have the right column types
    numerical_cols = df.select_dtypes(include=['number']).columns
    categorical_cols = df.select_dtypes(include=['object', 'category', 'string']).columns
    
    # Need at least one numerical column for most charts
    if len(numerical_cols) == 0:
        return False
    
    # For pie charts, need categorical + numerical
    if 'pie' in user_query.lower() and len(categorical_cols) == 0:
        return False
    
    return True

def generate_simple_display(df: pd.DataFrame, user_query: str) -> Dict[str, Any]:
    """
    Generate simple display for non-chartable data
    """
    if df.empty:
        return {
            "type": "text",
            "content": "No data available for the query.",
            "summary": "Empty result set"
        }
    
    num_rows = len(df)
    num_cols = len(df.columns)
    
    # For very small datasets, show as formatted text
    if num_rows <= 5 and num_cols <= 3:
        return {
            "type": "table",
            "content": df.to_dict(orient="records"),
            "summary": f"Found {num_rows} results with {num_cols} columns"
        }
    
    # For larger datasets, show summary statistics
    numerical_cols = df.select_dtypes(include=['number']).columns
    if len(numerical_cols) > 0:
        summary_stats = df[numerical_cols].describe()
        return {
            "type": "summary",
            "content": summary_stats.to_dict(),
            "summary": f"Dataset contains {num_rows} rows with {len(numerical_cols)} numerical columns"
        }
    
    # Default text summary
    return {
        "type": "text",
        "content": f"Query returned {num_rows} rows with {num_cols} columns",
        "summary": f"Results: {num_rows} rows × {num_cols} columns"
    }
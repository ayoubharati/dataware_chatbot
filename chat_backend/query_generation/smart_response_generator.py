"""
Smart Response Generator for Query Generation System (Modified to use Gemini analysis)
"""

import pandas as pd
import json
import logging
from typing import Dict, Any, List, Optional, Union
import sys
import os

# Add parent directory to path to import chart_generator and gemini_client
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from chart_generator import generate_plotly_chart
from gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class SmartResponseGenerator:
    """
    Generates appropriate responses for query results using Gemini's analysis.
    """
    
    def __init__(self):
        """Initialize the smart response generator with Gemini client."""
        self.gemini_client = GeminiClient()
        # Extended chart types to match Plotly capabilities
        self.supported_chart_types = [
            "bar", "line", "pie", "scatter", "histogram", "box", "area", 
            "bubble", "heatmap", "violin", "treemap", "sunburst", "funnel", 
            "waterfall", "gauge"
        ]
    
    def generate_response(self, user_query: str, sql_query: str, 
                         query_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate the complete response using Gemini's analysis.
        
        Args:
            user_query: The original user question
            sql_query: The final working SQL query
            query_results: The query execution results
            
        Returns:
            Dict with complete response structure
        """
        try:
            # Ensure query_results is a list of dictionaries
            if not isinstance(query_results, list):
                logger.warning(f"query_results is not a list: {type(query_results)}")
                if hasattr(query_results, 'to_dict'):
                    query_results = query_results.to_dict(orient="records")
                else:
                    query_results = []
            
            # Handle empty results
            if not query_results:
                logger.info("Query returned no results")
                return {
                    "resolvable": True,
                    "result_type": "text",
                    "query": sql_query,
                    "chart_data": None,
                    "result": "No data found for the query.",
                    "message": "Your query executed successfully but returned no results."
                }
            
            # Get Gemini's analysis
            gemini_result = self.gemini_client.generate_final_response_and_chart(
                user_query, sql_query, query_results
            )
            
            if not gemini_result["success"]:
                logger.error(f"Gemini analysis failed: {gemini_result['error']}")
                return self._generate_fallback_response(user_query, sql_query, query_results)
            
            # Parse Gemini's response
            parsed = gemini_result.get("parsed_response", {})
            
            result_type_raw = parsed.get("result_type")
            chart_type_raw = parsed.get("chart_type")

            result_type = result_type_raw.lower() if result_type_raw else ""
            chart_type = chart_type_raw.lower() if chart_type_raw else ""
            message = parsed.get("message", "")
            
            # Validate Gemini's analysis
            if not result_type or not message:
                logger.warning("Invalid Gemini response structure, using fallback")
                return self._generate_fallback_response(user_query, sql_query, query_results)
            
            # Generate response based on Gemini's analysis
            if result_type == "chart" and chart_type and chart_type != "n/a":
                return self._generate_chart_response_from_gemini(
                    query_results, sql_query, chart_type, message
                )
            elif result_type == "table":
                return self._generate_table_response(query_results, sql_query, message)
            else:  # text
                return self._generate_text_response(query_results, sql_query, message)
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._generate_fallback_response(user_query, sql_query, query_results)
    
    def _generate_chart_response_from_gemini(self, query_results: List[Dict[str, Any]], 
                                   sql_query: str, chart_type: str, 
                                   message: str) -> Dict[str, Any]:
        """Generate a chart response based on Gemini's analysis using Plotly."""
        try:
            # Handle None or empty chart_type
            if not chart_type or chart_type.lower() == "n/a":
                logger.warning("No chart type specified, falling back to table")
                return self._generate_table_response(query_results, sql_query, message)
            
            df = pd.DataFrame(query_results)
            
            # Map chart_type if needed (handle variations)
            normalized_chart_type = self._normalize_chart_type(chart_type)
            
            if normalized_chart_type not in self.supported_chart_types:
                logger.warning(f"Unsupported chart type: {chart_type}, falling back to bar")
                normalized_chart_type = "bar"
            
            # Create chart configuration
            config = self._create_chart_config_for_type(df, normalized_chart_type)
            
            # Generate Plotly chart instead of Chart.js
            chart_data = generate_plotly_chart(df, normalized_chart_type, config)
            
            return {
                "resolvable": True,
                "result_type": "chart",
                "query": sql_query,
                "chart_data": chart_data,
                "result": None,
                "message": message
            }
        
        except Exception as e:
            logger.error(f"Chart generation failed: {e}")
            # Fallback to table
            return self._generate_table_response(query_results, sql_query, message)
    
    def _generate_table_response(self, query_results: List[Dict[str, Any]], 
                                sql_query: str, message: str) -> Dict[str, Any]:
        """Generate a table response."""
        
        max_rows = 20
        limited_results = query_results[:max_rows]
        
        return {
            "resolvable": True,
            "result_type": "table",
            "query": sql_query,
            "chart_data": None,
            "result": limited_results,
            "message": message
        }
    
    def _generate_text_response(self, query_results: List[Dict[str, Any]], 
                               sql_query: str, message: str) -> Dict[str, Any]:
        """Generate a text response."""
        # For text responses, we might want to extract a simple value or summary
        result_content = self._extract_text_content(query_results)
        
        return {
            "resolvable": True,
            "result_type": "text",
            "query": sql_query,
            "chart_data": None,
            "result": result_content,
            "message": message
        }
    
    def _extract_text_content(self, query_results: List[Dict[str, Any]]) -> str:
        """Extract appropriate text content from query results."""
        try:
            if len(query_results) == 1:
                # Single row - might be a single value or summary
                row = query_results[0]
                if len(row) == 1:
                    # Single value
                    value = list(row.values())[0]
                    return str(value)
                else:
                    # Multiple columns in single row
                    return ", ".join([f"{k}: {v}" for k, v in row.items()])
            else:
                # Multiple rows - provide a count summary
                return f"Found {len(query_results)} results"
        except Exception as e:
            logger.error(f"Error extracting text content: {e}")
            return "Query completed successfully"
    
    def _normalize_chart_type(self, chart_type: str) -> str:
        """Normalize chart type to supported types."""
        chart_type = chart_type.lower().strip()
        
        # Handle common variations
        if chart_type in ["column", "columns"]:
            return "bar"
        elif chart_type in ["time_series", "timeseries"]:
            return "line"
        elif chart_type in ["donut", "doughnut"]:
            return "pie"
        elif chart_type in ["point", "points"]:
            return "scatter"
        
        return chart_type
    
    def _create_chart_config_for_type(self, df: pd.DataFrame, chart_type: str) -> Dict[str, Any]:
        """Create configuration for specific chart type."""
        config = {
            "title": f"Data Visualization",
            "responsive": True
        }
        
        # Basic configuration for common chart types
        if chart_type in ["bar", "line"] and len(df.columns) >= 2:
            config["xKey"] = df.columns[0]
            config["yKey"] = df.columns[1]
        elif chart_type == "pie" and len(df.columns) >= 2:
            config["nameKey"] = df.columns[0]
            config["valueKey"] = df.columns[1]
        elif chart_type == "scatter" and len(df.columns) >= 2:
            config["xKey"] = df.columns[0]
            config["yKey"] = df.columns[1]
        
        return config
    
    def _generate_fallback_response(self, user_query: str, sql_query: str, 
                                  query_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate fallback response when Gemini analysis fails."""
        try:
            if query_results:
                num_rows = len(query_results)
                return {
                    "resolvable": True,
                    "result_type": "table",
                    "query": sql_query,
                    "chart_data": None,
                    "result": query_results,
                    "message": f"Query executed successfully! Found {num_rows} rows of data."
                }
            else:
                return {
                    "resolvable": True,
                    "result_type": "text",
                    "query": sql_query,
                    "chart_data": None,
                    "result": "No data found",
                    "message": "Query executed successfully but returned no results."
                }
        except Exception as e:
            logger.error(f"Fallback response creation failed: {e}")
            return {
                "resolvable": False,
                "result_type": None,
                "query": sql_query,
                "chart_data": None,
                "result": None,
                "message": f"Query completed but response generation failed: {str(e)}"
            }
    
    def validate_response(self, response: Dict[str, Any]) -> bool:
        """Validate that the generated response has the correct structure."""
        required_fields = ["resolvable", "result_type", "query", "message"]
        
        # Check required fields exist
        for field in required_fields:
            if field not in response:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Check field types
        if not isinstance(response["resolvable"], bool):
            logger.error("resolvable must be boolean")
            return False
        
        if not isinstance(response["query"], str):
            logger.error("query must be string")
            return False
        
        if not isinstance(response["message"], str):
            logger.error("message must be string")
            return False
        
        # If resolvable, validate result_type specific requirements
        if response["resolvable"]:
            valid_result_types = ["chart", "table", "summary", "text", "number", "string"]
            if response["result_type"] not in valid_result_types:
                logger.error(f"Invalid result_type: {response['result_type']}")
                return False
            
            # Chart type requires chart_data
            if response["result_type"] == "chart":
                if "chart_data" not in response or response["chart_data"] is None:
                    logger.error("chart result_type requires chart_data")
                    return False
            
            # Other types require result field
            elif response["result_type"] in ["table", "summary", "text", "number", "string"]:
                if "result" not in response:
                    logger.error(f"{response['result_type']} result_type requires result field")
                    return False
        
        return True
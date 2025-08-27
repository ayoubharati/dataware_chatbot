"""
Query Tester for the Query Generation system.
Handles SQL execution, validation, and error handling with improved PostgreSQL compatibility.
"""

import logging
import time
import pandas as pd
from typing import Dict, Any, Optional, Tuple
import psycopg2
import psycopg2.extras
from sqlalchemy import create_engine, text
from config import DB_CONFIG

logger = logging.getLogger(__name__)

class QueryTester:
    """Tests SQL queries for execution and validation with improved PostgreSQL handling."""
    
    def __init__(self):
        """Initialize the query tester with database connection."""
        self.db_engine = None
        self.connection_string = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database connection for query testing."""
        try:
            # Create connection string
            self.connection_string = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
            
            # Create engine with specific settings to avoid immutabledict issues
            self.db_engine = create_engine(
                self.connection_string, 
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False,
                # Add these parameters to handle the immutabledict issue
                connect_args={
                    "options": "-c timezone=UTC"
                }
            )
            
            # Test connection
            with self.db_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("Database connection initialized for query testing")
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            self.db_engine = None
    
    def is_ready(self) -> bool:
        """Check if the database connection is ready."""
        return self.db_engine is not None
    
    def test_query_execution(self, sql_query: str, preview_limit: int = 10000) -> Dict[str, Any]:
        """
        Test if a SQL query executes successfully using raw psycopg2 to avoid SQLAlchemy issues.
        
        Args:
            sql_query: The SQL query to test
            preview_limit: Maximum number of rows to return in preview
            
        Returns:
            Dictionary containing execution results and metadata
        """
        if not self.is_ready():
            return {
                "success": False,
                "error": "Database connection not available",
                "execution_time": 0
            }
        
        # Try raw psycopg2 approach first
        try:
            logger.info(f"Testing SQL query execution: {sql_query[:100]}...")
            start_time = time.time()
            
            # Use raw psycopg2 connection to avoid SQLAlchemy immutabledict issues
            conn = psycopg2.connect(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                database=DB_CONFIG['database'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password']
            )
            
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(sql_query)
            
            # Fetch results
            rows = cursor.fetchall()
            execution_time = time.time() - start_time
            
            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Convert to list of dicts for consistency
            preview = []
            for row in rows[:preview_limit]:
                preview.append(dict(row))
            
            # Create DataFrame from the results for compatibility
            if rows:
                df = pd.DataFrame([dict(row) for row in rows])
            else:
                df = pd.DataFrame()
            
            cursor.close()
            conn.close()
            
            result = {
                "success": True,
                "df": df,
                "columns": columns,
                "row_count": len(rows),
                "preview": preview,
                "execution_time": execution_time,
                "sql_query": sql_query
            }
            
            logger.info(f"Query executed successfully in {execution_time:.3f}s, returned {len(rows)} rows")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time if 'start_time' in locals() else 0
            error_msg = str(e)
            
            logger.error(f"Raw psycopg2 query execution failed: {error_msg}")
            
            # Fallback to SQLAlchemy with text() wrapper
            try:
                logger.info("Trying SQLAlchemy fallback...")
                start_time = time.time()
                
                # Use text() to properly handle the query
                with self.db_engine.connect() as connection:
                    result_proxy = connection.execute(text(sql_query))
                    
                    # Fetch all results
                    rows = result_proxy.fetchall()
                    columns = list(result_proxy.keys())
                    
                    # Convert to list of dicts
                    preview = []
                    for row in rows[:preview_limit]:
                        preview.append(dict(zip(columns, row)))
                    
                    # Create DataFrame
                    if rows:
                        df = pd.DataFrame([dict(zip(columns, row)) for row in rows])
                    else:
                        df = pd.DataFrame()
                    
                    execution_time = time.time() - start_time
                
                result = {
                    "success": True,
                    "df": df,
                    "columns": columns,
                    "row_count": len(rows),
                    "preview": preview,
                    "execution_time": execution_time,
                    "sql_query": sql_query
                }
                
                logger.info(f"SQLAlchemy fallback successful in {execution_time:.3f}s, returned {len(rows)} rows")
                return result
                
            except Exception as fallback_error:
                execution_time = time.time() - start_time if 'start_time' in locals() else 0
                logger.error(f"SQLAlchemy fallback also failed: {str(fallback_error)}")
                
                return {
                    "success": False,
                    "error": f"Both psycopg2 and SQLAlchemy failed. Original: {error_msg}, Fallback: {str(fallback_error)}",
                    "df": pd.DataFrame(),
                    "columns": [],
                    "row_count": 0,
                    "preview": [],
                    "execution_time": execution_time,
                    "sql_query": sql_query
                }
    
    def validate_query_syntax(self, sql_query: str) -> Tuple[bool, str]:
        """
        Validate SQL query syntax without executing it using EXPLAIN.
        
        Args:
            sql_query: The SQL query to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.is_ready():
            return False, "Database connection not available"
        
        try:
            # Use EXPLAIN to validate syntax without executing
            explain_query = f"EXPLAIN {sql_query}"
            
            conn = psycopg2.connect(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                database=DB_CONFIG['database'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password']
            )
            
            cursor = conn.cursor()
            cursor.execute(explain_query)
            cursor.fetchall()  # Consume results
            cursor.close()
            conn.close()
            
            return True, ""
            
        except Exception as e:
            return False, f"Syntax error: {str(e)}"
    
    def get_query_metadata(self, sql_query: str) -> Dict[str, Any]:
        """
        Get metadata about a query without executing it.
        
        Args:
            sql_query: The SQL query to analyze
            
        Returns:
            Dictionary containing query metadata
        """
        metadata = {
            "query_type": "unknown",
            "tables_mentioned": [],
            "columns_mentioned": [],
            "has_joins": False,
            "has_aggregations": False,
            "has_subqueries": False,
            "estimated_complexity": "low"
        }
        
        try:
            sql_upper = sql_query.upper()
            
            # Determine query type
            if sql_upper.startswith("SELECT"):
                metadata["query_type"] = "SELECT"
            elif sql_upper.startswith("INSERT"):
                metadata["query_type"] = "INSERT"
            elif sql_upper.startswith("UPDATE"):
                metadata["query_type"] = "UPDATE"
            elif sql_upper.startswith("DELETE"):
                metadata["query_type"] = "DELETE"
            
            # Check for joins
            if "JOIN" in sql_upper:
                metadata["has_joins"] = True
            
            # Check for aggregations
            if any(func in sql_upper for func in ["COUNT(", "SUM(", "AVG(", "MAX(", "MIN(", "GROUP BY"]):
                metadata["has_aggregations"] = True
            
            # Check for subqueries
            if "(" in sql_query and "SELECT" in sql_query[sql_query.find("("):]:
                metadata["has_subqueries"] = True
            
            # Estimate complexity
            complexity_score = 0
            if metadata["has_joins"]:
                complexity_score += 2
            if metadata["has_aggregations"]:
                complexity_score += 1
            if metadata["has_subqueries"]:
                complexity_score += 2
            
            if complexity_score <= 1:
                metadata["estimated_complexity"] = "low"
            elif complexity_score <= 3:
                metadata["estimated_complexity"] = "medium"
            else:
                metadata["estimated_complexity"] = "high"
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to analyze query metadata: {e}")
            return metadata
    
    def analyze_query_results(self, query_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the results of a successful query execution.
        
        Args:
            query_results: Results from test_query_execution
            
        Returns:
            Dictionary containing analysis results
        """
        if not query_results.get("success", False):
            return {"error": "Query execution was not successful"}
        
        try:
            df = query_results["df"]
            analysis = {
                "row_count": len(df),
                "column_count": len(df.columns),
                "data_types": {},
                "null_counts": {},
                "unique_counts": {},
                "sample_values": {},
                "is_empty": df.empty,
                "has_duplicates": len(df) != len(df.drop_duplicates()) if not df.empty else False
            }
            
            if not df.empty:
                # Analyze each column
                for col in df.columns:
                    analysis["data_types"][col] = str(df[col].dtype)
                    analysis["null_counts"][col] = df[col].isnull().sum()
                    analysis["unique_counts"][col] = df[col].nunique()
                    
                    # Get sample values (non-null)
                    non_null_values = df[col].dropna()
                    if len(non_null_values) > 0:
                        sample_size = min(3, len(non_null_values))
                        analysis["sample_values"][col] = non_null_values.head(sample_size).tolist()
                    else:
                        analysis["sample_values"][col] = []
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze query results: {e}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    def check_result_quality(self, query_results: Dict[str, Any], user_query: str) -> Dict[str, Any]:
        """
        Check the quality of query results against user intent.
        
        Args:
            query_results: Results from test_query_execution
            user_query: The original user query
            
        Returns:
            Dictionary containing quality assessment
        """
        if not query_results.get("success", False):
            return {"quality_score": 0, "issues": ["Query execution failed"]}
        
        try:
            analysis = self.analyze_query_results(query_results)
            quality_score = 100
            issues = []
            
            # Check for empty results
            if analysis.get("is_empty", True):
                quality_score -= 50
                issues.append("Query returned no results")
            
            # Check for reasonable row count
            row_count = analysis.get("row_count", 0)
            if row_count > 10000:
                quality_score -= 20
                issues.append(f"Query returned {row_count} rows (potentially too many)")
            elif row_count == 0:
                quality_score -= 30
                issues.append("Query returned no data")
            
            # Check for null values
            null_columns = [col for col, null_count in analysis.get("null_counts", {}).items() 
                          if null_count > 0]
            if null_columns:
                quality_score -= 10
                issues.append(f"Found null values in columns: {null_columns}")
            
            # Check for data variety
            low_variety_cols = [col for col, unique_count in analysis.get("unique_counts", {}).items() 
                              if unique_count <= 1]
            if low_variety_cols:
                quality_score -= 15
                issues.append(f"Low variety in columns: {low_variety_cols}")
            
            # Ensure quality score doesn't go below 0
            quality_score = max(0, quality_score)
            
            return {
                "quality_score": quality_score,
                "issues": issues,
                "analysis": analysis,
                "recommendations": self._generate_quality_recommendations(issues, analysis)
            }
            
        except Exception as e:
            logger.error(f"Failed to check result quality: {e}")
            return {"quality_score": 0, "issues": [f"Quality check failed: {str(e)}"]}
    
    def _generate_quality_recommendations(self, issues: list, analysis: Dict[str, Any]) -> list:
        """Generate recommendations for improving query quality."""
        recommendations = []
        
        if "Query returned no results" in issues:
            recommendations.append("Consider relaxing WHERE conditions or checking data availability")
        
        if "Query returned too many rows" in issues:
            recommendations.append("Add LIMIT clause or more specific WHERE conditions")
        
        if "Found null values" in issues:
            recommendations.append("Consider handling NULL values with COALESCE or IS NOT NULL")
        
        if "Low variety in columns" in issues:
            recommendations.append("Check if filtering is too restrictive or if data is uniform")
        
        return recommendations
    
    def cleanup(self):
        """Clean up database connections."""
        if self.db_engine:
            self.db_engine.dispose()
            logger.info("Database connections cleaned up")
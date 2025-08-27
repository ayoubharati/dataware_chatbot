"""
Query Orchestrator for the Query Generation system.
Coordinates the entire workflow from term extraction to query validation.
"""

import time
import logging
import json
import os
import re
from typing import Dict, Any, List
import datetime
from datetime import date
# Add parent directory to path for imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import MAX_RETRY_ATTEMPTS
from config import SCHEMA_FILE_PATH
from extract_words import extract_search_terms
from search_using_fiass import MultiTableEmbeddingSearch
from gemini_client import GeminiClient
from query_tester import QueryTester
from smart_response_generator import SmartResponseGenerator

logger = logging.getLogger(__name__)

class QueryOrchestrator:
    """
    Orchestrates the complete 7-step query generation workflow.
    
    Steps:
    1. Load schema and description
    2. Extract contextual search terms
    3. Perform FAISS searches
    4. Check initial resolvability
    5. Generate initial SQL query
    6. Test and validate query
    7. Generate final response and chart
    """
    
    def __init__(self):
        """Initialize all components for the workflow."""
        self.gemini_client = GeminiClient()
        self.query_tester = QueryTester()
        self.smart_response_generator = SmartResponseGenerator()
        
        # Debug logging setup
        self.debug_log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "debug_logs")
        os.makedirs(self.debug_log_dir, exist_ok=True)
    
    def _sanitize_filename(self, text: str) -> str:
        """Sanitize text to create a valid filename."""
        # Remove or replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', text)
        # Limit length and remove extra spaces
        sanitized = re.sub(r'\s+', '_', sanitized.strip())
        # Limit to 50 characters
        return sanitized[:50]
    
    def _create_debug_log(self, user_query: str) -> str:
        """Create a debug log file for this query."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_query = self._sanitize_filename(user_query)
        filename = f"{timestamp}_{sanitized_query}.txt"
        filepath = os.path.join(self.debug_log_dir, filename)
        return filepath
    
    def _log_to_debug_file(self, filepath: str, content: str, section: str = ""):
        """Log content to debug file with section headers."""
        try:
            with open(filepath, 'a', encoding='utf-8') as f:
                if section:
                    f.write(f"\n{'='*80}\n")
                    f.write(f"🔍 {section.upper()}\n")
                    f.write(f"{'='*80}\n")
                f.write(f"{content}\n")
        except Exception as e:
            logger.error(f"Failed to write to debug file: {e}")
    
    def _log_step_to_debug_file(self, filepath: str, step_name: str, step_data: Dict[str, Any]):
        """Log a complete step to debug file."""
        try:
            # Custom JSON encoder to handle date objects
            class DateTimeEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, (datetime.date, datetime.datetime)):
                        return obj.isoformat()
                    return super().default(obj)
            
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"📋 STEP: {step_name.upper()}\n")
                f.write(f"{'='*80}\n")
                f.write(f"⏱️  Duration: {step_data.get('duration', 'N/A')}s\n")
                f.write(f"✅ Success: {step_data.get('success', 'N/A')}\n")
                
                if step_data.get('success'):
                    # Log step-specific data with proper date serialization
                    if step_name == "extract_terms":
                        f.write(f"🔍 Extracted Terms: {step_data.get('extracted_terms', [])}\n")
                    elif step_name == "faiss_search":
                        f.write(f"🔎 FAISS Summary: {step_data.get('faiss_summary', 'N/A')}\n")
                    elif step_name == "resolvability_check":
                        f.write(f"🎯 Resolvable: {step_data.get('resolvable', 'N/A')}\n")
                        f.write(f"💬 Message: {step_data.get('message', 'N/A')}\n")
                        f.write(f"🧠 Reasoning: {step_data.get('reasoning', 'N/A')}\n")
                    elif step_name == "generate_initial_query":
                        f.write(f"📝 SQL Query: {step_data.get('sql_query', 'N/A')}\n")
                        f.write(f"🤖 Gemini Response: {step_data.get('gemini_response', 'N/A')}\n")
                    elif step_name == "test_and_validate":
                        f.write(f"🧪 Final SQL: {step_data.get('final_sql', 'N/A')}\n")
                        # Use custom encoder for date serialization
                        execution_result = step_data.get('execution_result', {})
                        f.write(f"📊 Execution Result: {json.dumps(execution_result, indent=2, cls=DateTimeEncoder)}\n")
                    elif step_name == "generate_final_response":
                        final_response = step_data.get('final_response', {})
                        f.write(f"🎨 Final Response: {json.dumps(final_response, indent=2, cls=DateTimeEncoder)}\n")
                else:
                    f.write(f"❌ Error: {step_data.get('error', 'Unknown error')}\n")
                
                f.write(f"\n")
        except Exception as e:
            logger.error(f"Failed to log step to debug file: {e}")
    
    def _log_gemini_interaction(self, filepath: str, step_name: str, prompt: str, response: str):
        """Log Gemini prompt and response."""
        try:
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"🤖 GEMINI INTERACTION: {step_name.upper()}\n")
                f.write(f"{'='*80}\n")
                f.write(f"📤 PROMPT:\n")
                f.write(f"{prompt}\n")
                f.write(f"\n📥 RESPONSE:\n")
                f.write(f"{response}\n")
                f.write(f"\n")
        except Exception as e:
            logger.error(f"Failed to log Gemini interaction: {e}")
    
    def generate_query_workflow(self, user_query: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Execute the complete 7-step query generation workflow.
        
        Args:
            user_query: The user's natural language query
            max_retries: Maximum number of retry attempts for query correction
            
        Returns:
            Dict containing the complete workflow results
        """
        # Create debug log file
        debug_filepath = self._create_debug_log(user_query)
        
        # Log initial query
        self._log_to_debug_file(debug_filepath, f"🚀 QUERY WORKFLOW START\n", "WORKFLOW START")
        self._log_to_debug_file(debug_filepath, f"📝 User Query: {user_query}")
        self._log_to_debug_file(debug_filepath, f"⏰ Start Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._log_to_debug_file(debug_filepath, f"🔄 Max Retries: {max_retries}")
        
        workflow_start = time.time()
        workflow_results = {
            "user_query": user_query,
            "steps": [],
            "success": False,
            "final_result": None,
            "total_workflow_time": 0
        }
        
        try:
            # Step 1: Load schema and description
            step1_result = self._step1_load_schema()
            workflow_results["steps"].append(step1_result)
            self._log_step_to_debug_file(debug_filepath, "load_schema", step1_result)
            
            if not step1_result["success"]:
                self._log_to_debug_file(debug_filepath, f"❌ Workflow failed at Step 1: {step1_result['error']}")
                return self._create_error_result(workflow_results, "Schema loading failed", step1_result["error"])
            
            # Step 2: Extract contextual search terms
            step2_result = self._step2_extract_terms(user_query, step1_result["schema_description"])
            workflow_results["steps"].append(step2_result)
            self._log_step_to_debug_file(debug_filepath, "extract_terms", step2_result)
            
            if not step2_result["success"]:
                self._log_to_debug_file(debug_filepath, f"❌ Workflow failed at Step 2: {step2_result['error']}")
                return self._create_error_result(workflow_results, "Term extraction failed", step2_result["error"])
            
            # Step 3: Perform FAISS searches
            step3_result = self._step3_faiss_search(user_query, step2_result["extracted_terms"])
            workflow_results["steps"].append(step3_result)
            self._log_step_to_debug_file(debug_filepath, "faiss_search", step3_result)
            
            if not step3_result["success"]:
                self._log_to_debug_file(debug_filepath, f"❌ Workflow failed at Step 3: {step3_result['error']}")
                return self._create_error_result(workflow_results, "FAISS search failed", step3_result["error"])
            
            # Step 4: Check initial resolvability
            step4_result = self._step4_check_resolvability(user_query, step1_result["schema_description"], step3_result["faiss_summary"])
            workflow_results["steps"].append(step4_result)
            self._log_step_to_debug_file(debug_filepath, "resolvability_check", step4_result)
            
            # Log Gemini interaction for resolvability check
            if step4_result.get("prompt") and step4_result.get("gemini_response"):
                self._log_gemini_interaction(debug_filepath, "resolvability_check", 
                                           step4_result["prompt"], step4_result["gemini_response"])
            
            if not step4_result["success"]:
                self._log_to_debug_file(debug_filepath, f"❌ Workflow failed at Step 4: {step4_result['error']}")
                return self._create_error_result(workflow_results, "Resolvability check failed", step4_result["error"])
            
            # Check if query is resolvable
            if not step4_result.get("resolvable", False):
                self._log_to_debug_file(debug_filepath, f"❌ Query marked as unresolvable: {step4_result['message']}")
                workflow_results["success"] = False
                workflow_results["final_result"] = {
                    "resolvable": False,
                    "message": step4_result["message"],
                    "reasoning": step4_result.get("reasoning", ""),
                    "step": "resolvability_check"
                }
                return workflow_results
            
            # Step 5: Generate initial SQL query
            step5_result = self._step5_generate_initial_query(user_query, step1_result["schema_description"], step3_result["faiss_summary"])
            workflow_results["steps"].append(step5_result)
            self._log_step_to_debug_file(debug_filepath, "generate_initial_query", step5_result)
            
            # Log Gemini interaction for initial query generation
            if step5_result.get("prompt") and step5_result.get("gemini_response"):
                self._log_gemini_interaction(debug_filepath, "generate_initial_query", 
                                           step5_result["prompt"], step5_result["gemini_response"])
            
            if not step5_result["success"]:
                self._log_to_debug_file(debug_filepath, f"❌ Workflow failed at Step 5: {step5_result['error']}")
                return self._create_error_result(workflow_results, "Initial query generation failed", step5_result["error"])
            
            # Extract SQL query
            sql_query = step5_result.get("sql_query", "").strip()
            if not sql_query:
                self._log_to_debug_file(debug_filepath, f"❌ No SQL query generated")
                return self._create_error_result(workflow_results, "No SQL query generated", "Empty SQL response")
            
            # Step 6: Test and validate query
            step6_result = self._step6_test_and_validate(
                user_query,
                sql_query,
                step1_result["schema_description"],
                step3_result["faiss_summary"],
                max_retries
            )
            workflow_results["steps"].append(step6_result)
            self._log_step_to_debug_file(debug_filepath, "test_and_validate", step6_result)
            
            if not step6_result["success"]:
                self._log_to_debug_file(debug_filepath, f"❌ Workflow failed at Step 6: {step6_result['error']}")
                return self._create_error_result(workflow_results, "Query testing/validation failed", step6_result["error"])
            
            # Step 7: Generate final response and chart
            step7_result = self._step7_generate_final_response(
                user_query,
                step6_result["final_sql"],
                step6_result["execution_result"]["preview"]
            )
            workflow_results["steps"].append(step7_result)
            self._log_step_to_debug_file(debug_filepath, "generate_final_response", step7_result)
            
            if not step7_result["success"]:
                self._log_to_debug_file(debug_filepath, f"❌ Workflow failed at Step 7: {step7_result['error']}")
                return self._create_error_result(workflow_results, "Final response generation failed", step7_result["error"])
            
            # Set final result
            workflow_results["final_result"] = step7_result["final_response"]
            workflow_results["success"] = True
            
            # Clean up workflow results to ensure JSON serialization
            workflow_results = self._cleanup_workflow_results(workflow_results)
            
            # Log successful completion
            self._log_to_debug_file(debug_filepath, f"✅ Workflow completed successfully!")
            self._log_to_debug_file(debug_filepath, f"📊 Final Result: {json.dumps(workflow_results['final_result'], indent=2)}")
            
        except Exception as e:
            logger.error(f"❌ Workflow failed with exception: {e}")
            self._log_to_debug_file(debug_filepath, f"❌ Workflow failed with exception: {e}")
            error_result = {
                "step": "workflow_exception",
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            }
            workflow_results["steps"].append(error_result)
            workflow_results["final_result"] = error_result
            workflow_results["success"] = False
        
        finally:
            workflow_results["total_workflow_time"] = time.time() - workflow_start
            
            # Ensure final result is serializable
            try:
                # Define DateTimeEncoder class here for the test
                class DateTimeEncoder(json.JSONEncoder):
                    def default(self, obj):
                        if isinstance(obj, (datetime.date, datetime.datetime)):
                            return obj.isoformat()
                        return super().default(obj)
                
                # Test serialization with custom encoder
                json.dumps(workflow_results, cls=DateTimeEncoder)
            except Exception as e:
                logger.warning(f"Workflow results not fully serializable: {e}")
                # Clean up again to ensure serialization
                workflow_results = self._cleanup_workflow_results(workflow_results)
            
            self._log_to_debug_file(debug_filepath, f"Total Workflow Time: {workflow_results['total_workflow_time']:.3f}s")
            self._log_to_debug_file(debug_filepath, f"Workflow completed in {workflow_results['total_workflow_time']:.3f}s", "WORKFLOW END")
            logger.info(f"Workflow completed in {workflow_results['total_workflow_time']:.3f}s")
        
        return workflow_results

    def _step1_load_schema(self) -> Dict[str, Any]:
        """Step 1: Load database schema and description directly from markdown file."""
        step_start = time.time()
        
        try:
            logger.info("📚 Step 1: Loading database schema and description...")
            
            # Get schema file path from config
            
            # Load schema directly from file
            if not os.path.exists(SCHEMA_FILE_PATH):
                return {
                    "step": "load_schema",
                    "success": False,
                    "error": f"Schema file not found: {SCHEMA_FILE_PATH}",
                    "timestamp": step_start,
                    "duration": time.time() - step_start
                }
            
            try:
                with open(SCHEMA_FILE_PATH, 'r', encoding='utf-8') as f:
                    schema_description = f.read()
            except Exception as read_error:
                return {
                    "step": "load_schema",
                    "success": False,
                    "error": f"Failed to read schema file: {str(read_error)}",
                    "timestamp": step_start,
                    "duration": time.time() - step_start
                }
            
            if not schema_description.strip():
                return {
                    "step": "load_schema",
                    "success": False,
                    "error": "Schema file is empty",
                    "timestamp": step_start,
                    "duration": time.time() - step_start
                }
            
            result = {
                "step": "load_schema",
                "success": True,
                "schema_description": schema_description,
                "timestamp": step_start,
                "duration": time.time() - step_start
            }
            
            logger.info(f"✅ Step 1 completed: Schema loaded successfully from {SCHEMA_FILE_PATH}")
            return result
        
        except Exception as e:
            logger.error(f"❌ Step 1 failed: {e}")
            return {
                "step": "load_schema",
                "success": False,
                "error": str(e),
                "timestamp": step_start,
                "duration": time.time() - step_start
            }

    def _step2_extract_terms(self, user_query: str, schema_description: str) -> Dict[str, Any]:
        """Step 2: Extract contextual search terms from user query."""
        step_start = time.time()
        
        try:
            logger.info("🔍 Step 2: Extracting contextual search terms...")
            
            # Extract terms with fallback
            extracted_terms = extract_search_terms(user_query, schema_description)

            
            if not extracted_terms:
                return {
                    "step": "extract_terms",
                    "success": False,
                    "error": "Failed to extract search terms",
                    "timestamp": step_start,
                    "duration": time.time() - step_start
                }
            
            result = {
                "step": "extract_terms",
                "success": True,
                "extracted_terms": extracted_terms,
                "timestamp": step_start,
                "duration": time.time() - step_start
            }
            
            logger.info(f"✅ Step 2 completed: Extracted {len(extracted_terms)} terms")
            return result
            
        except Exception as e:
            logger.error(f"❌ Step 2 failed: {e}")
            return {
                "step": "extract_terms",
                "success": False,
                "error": str(e),
                "timestamp": step_start,
                "duration": time.time() - step_start
            }

    def _step3_faiss_search(self, user_query: str, extracted_terms: list) -> Dict[str, Any]:
        """Step 3: Perform FAISS searches on terms and whole query using the standalone functions."""
        step_start = time.time()

        try:
            logger.info("🔎 Step 3: Performing FAISS searches...")
        
            # Initialize the search class
            search_instance = MultiTableEmbeddingSearch()
            search_instance.load_all_embeddings()
            
            # Search on individual terms
            per_term_results = search_instance.search_multiple_terms(extracted_terms, top_k=10)
            
            # Search on whole query
            whole_query_results = search_instance.search(user_query, top_k=10)

            # Create simple FAISS summary for LLM analysis
            try:
                # Parse whole query results 
                whole_query_parsed = json.loads(whole_query_results)
                
                summary_parts = []
                
                # Add individual term results
                for term, results in per_term_results.items():
                    summary_parts.append(f"{term}:")
                    summary_parts.append(json.dumps(results, indent=2, default=str))
                    summary_parts.append("")  # Empty line for separation
                
                # Add whole query results
                summary_parts.append(f"{user_query}:")
                summary_parts.append(json.dumps(whole_query_parsed, indent=2, default=str))
                
                faiss_summary = "\n".join(summary_parts)
                
            except Exception as e:
                logger.error(f"Failed to create FAISS summary: {e}")
                faiss_summary = f"Error creating FAISS summary: {str(e)}"

            result = {
                "step": "faiss_search",
                "success": True,
                "per_term_results": per_term_results,
                "whole_query_results": json.loads(whole_query_results),  # search returns JSON string
                "faiss_summary": faiss_summary,
                "timestamp": step_start,
                "duration": time.time() - step_start,
            }

            logger.info("✅ Step 3 completed: FAISS searches completed")
            return result

        except Exception as e:
            logger.error(f"❌ Step 3 failed: {e}")
            return {
                "step": "faiss_search",
                "success": False,
                "error": str(e),
                "timestamp": step_start,
                "duration": time.time() - step_start,
            }



    def _step4_check_resolvability(self, user_query: str, schema_description: str, faiss_summary: str) -> Dict[str, Any]:
        """Step 4: Check if the user query is resolvable with available data."""
        step_start = time.time()
        
        try:
            logger.info("🎯 Step 4: Checking query resolvability...")
            
            # Check resolvability with Gemini
            resolvability_result = self.gemini_client.check_initial_resolvability(
                user_query, schema_description, faiss_summary
            )
            
            if not resolvability_result["success"]:
                return {
                    "step": "resolvability_check",
                    "success": False,
                    "error": resolvability_result["error"],
                    "timestamp": step_start,
                    "duration": time.time() - step_start
                }
            
            parsed = resolvability_result.get("parsed_response", {})
            
            result = {
                "step": "resolvability_check",
                "success": True,
                "resolvable": parsed.get("resolvable") == "yes",
                "message": parsed.get("message", "No message provided"),
                "reasoning": parsed.get("reasoning", "No reasoning provided"),
                "prompt": resolvability_result.get("prompt", ""),
                "gemini_response": resolvability_result.get("gemini_response", ""),
                "timestamp": step_start,
                "duration": time.time() - step_start
            }
            
            logger.info(f"✅ Step 4 completed: Query resolvable = {result['resolvable']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Step 4 failed: {e}")
            return {
                "step": "resolvability_check",
                "success": False,
                "error": str(e),
                "timestamp": step_start,
                "duration": time.time() - step_start
            }

    def _step5_generate_initial_query(self, user_query: str, schema_description: str, faiss_summary: str) -> Dict[str, Any]:
        """Step 5: Generate initial SQL query using Gemini."""
        step_start = time.time()
        
        try:
            logger.info("📝 Step 5: Generating initial SQL query...")
            
            # Generate initial SQL query
            query_result = self.gemini_client.generate_initial_query(
                user_query, schema_description, faiss_summary
            )
            
            if not query_result["success"]:
                return {
                    "step": "generate_initial_query",
                    "success": False,
                    "error": query_result["error"],
                    "timestamp": step_start,
                    "duration": time.time() - step_start
                }
            
            sql_query = query_result.get("sql_query", "").strip()
            
            if not sql_query:
                return {
                    "step": "generate_initial_query",
                    "success": False,
                    "error": "No SQL query generated",
                    "timestamp": step_start,
                    "duration": time.time() - step_start
                }
            
            result = {
                "step": "generate_initial_query",
                "success": True,
                "sql_query": sql_query,
                "prompt": query_result.get("prompt", ""),
                "gemini_response": query_result.get("gemini_response", ""),
                "timestamp": step_start,
                "duration": time.time() - step_start
            }
            
            logger.info(f"✅ Step 5 completed: SQL query generated successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ Step 5 failed: {e}")
            return {
                "step": "generate_initial_query",
                "success": False,
                "error": str(e),
                "timestamp": step_start,
                "duration": time.time() - step_start
            }

    def _step6_test_and_validate(self, user_query: str, sql_query: str, 
                        schema_description: str, faiss_summary: str, 
                        max_retries: int) -> Dict[str, Any]:
        """Step 6: Test query execution and retry until it runs without compilation errors."""
        step_start = time.time()
        
        try:
            logger.info("Testing and validating query...")
            
            retry_count = 0
            current_sql = sql_query
            last_error = None
            
            while retry_count <= max_retries:
                try:
                    # Test query execution
                    execution_result = self.query_tester.test_query_execution(current_sql)
                    
                    if execution_result["success"]:
                        # Query executed successfully - convert DataFrame to serializable format and return
                        serializable_result = execution_result.copy()
                        if "df" in serializable_result:
                            # Convert DataFrame to records format for JSON serialization
                            serializable_result["results"] = serializable_result["df"].to_dict(orient="records")
                            serializable_result["preview"] = serializable_result["results"]  # Add preview field
                            del serializable_result["df"]  # Remove the DataFrame
                        
                        result = {
                            "step": "test_and_validate",
                            "success": True,
                            "final_sql": current_sql,
                            "execution_result": serializable_result,
                            "retry_count": retry_count,
                            "timestamp": step_start,
                            "duration": time.time() - step_start
                        }
                        
                        logger.info(f"Query validated successfully after {retry_count} retries")
                        return result
                        
                    else:
                        # Query execution failed due to compilation error
                        last_error = execution_result["error"]
                        logger.info(f"Query execution failed (attempt {retry_count + 1}): {last_error}")
                        
                        if retry_count >= max_retries:
                            # Reached max retries
                            break
                        
                        # Attempt correction
                        logger.info("Attempting query correction...")
                        correction_result = self._correct_failed_query(
                            user_query, current_sql, last_error,
                            schema_description, faiss_summary
                        )
                        
                        if correction_result["success"]:
                            # Got a corrected query, use it for next iteration
                            current_sql = correction_result["corrected_sql"]
                            retry_count += 1
                            logger.info(f"Received corrected query for retry {retry_count}")
                        else:
                            # Correction failed
                            logger.error(f"Query correction failed: {correction_result['error']}")
                            break
                            
                except Exception as e:
                    last_error = str(e)
                    logger.error(f"Error during query testing (attempt {retry_count + 1}): {e}")
                    
                    if retry_count >= max_retries:
                        break
                        
                    # Try to correct this error too
                    correction_result = self._correct_failed_query(
                        user_query, current_sql, last_error,
                        schema_description, faiss_summary
                    )
                    
                    if correction_result["success"]:
                        current_sql = correction_result["corrected_sql"]
                        retry_count += 1
                    else:
                        break
            
            # If we get here, all retries failed
            return {
                "step": "test_and_validate",
                "success": False,
                "error": f"Failed to generate valid query after {max_retries} retries. Last error: {last_error}",
                "final_sql": current_sql,
                "retry_count": retry_count,
                "timestamp": step_start,
                "duration": time.time() - step_start
            }
            
        except Exception as e:
            logger.error(f"Step 6 failed with exception: {e}")
            return {
                "step": "test_and_validate",
                "success": False,
                "error": str(e),
                "timestamp": step_start,
                "duration": time.time() - step_start
            }
   
    def _step7_generate_final_response(self, user_query: str, final_sql: str, 
                                  query_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Step 7: Generate final response and chart using Gemini-powered smart response generator."""
        step_start = time.time()
        
        try:
            logger.info("Step 7: Generating final response and chart...")
            
            # Use smart response generator (which now uses Gemini internally)
            final_response = self.smart_response_generator.generate_response(
                user_query, final_sql, query_results
            )
            
            # Validate the response structure
            if not self.smart_response_generator.validate_response(final_response):
                logger.warning("Generated response failed validation, using fallback")
                final_response = self._create_fallback_response(user_query, final_sql, query_results)
            
            result = {
                "step": "generate_final_response",
                "success": True,
                "final_response": final_response,
                "timestamp": step_start,
                "duration": time.time() - step_start
            }
            
            logger.info(f"Step 7 completed successfully")
            logger.info(f"   Result type: {final_response.get('result_type', 'unknown')}")
            logger.info(f"   Resolvable: {final_response.get('resolvable', False)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Step 7 failed: {e}")
            return {
                "step": "generate_final_response", 
                "success": False,
                "error": f"Final response generation failed: {str(e)}",
                "final_response": self._create_fallback_response(user_query, final_sql, query_results),
                "timestamp": step_start,
                "duration": time.time() - step_start
            }
    
    def _create_fallback_response(self, user_query: str, final_sql: str, 
                                 query_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a fallback response if the smart generator fails."""
        try:
            # Simple fallback - convert results to basic format
            if query_results:
                num_rows = len(query_results)
                num_cols = len(query_results[0]) if query_results else 0
                
                return {
                    "resolvable": True,
                    "result_type": "table",
                    "query": final_sql,
                    "chart_data": None,
                    "result": query_results,
                    "message": f"Query executed successfully! Found {num_rows} rows with {num_cols} columns."
                }
            else:
                return {
                    "resolvable": True,
                    "result_type": "text",
                    "query": final_sql,
                    "chart_data": None,
                    "result": "No data found for the query.",
                    "message": "Query executed successfully but returned no results."
                }
        except Exception as e:
            logger.error(f"Fallback response creation failed: {e}")
            return {
                "resolvable": False,
                "result_type": None,
                "query": final_sql,
                "chart_data": None,
                "result": None,
                "message": f"Query executed but response generation failed: {str(e)}"
            }

    # def _validate_query_results(self, user_query: str, sql_query: str, 
    #                            execution_result: Dict[str, Any], 
    #                            schema_description: str, faiss_summary: str) -> Dict[str, Any]:
    #     """Validate if query results match user intent."""
    #     try:
    #         # Ensure execution_result is already JSON-serializable (should be handled in step 6)
    #         # Use Gemini to validate results
    #         validation_result = self.gemini_client.validate_query_results(
    #             user_query, sql_query, execution_result, schema_description, faiss_summary
    #         )
            
    #         return validation_result
            
    #     except Exception as e:
    #         logger.error(f"❌ Query validation failed: {e}")
    #         return {"valid": False, "reason": f"Validation failed: {str(e)}"}

    def _correct_failed_query(self, user_query: str, failed_sql: str, error_message: str,
                         schema_description: str, faiss_summary: str) -> Dict[str, Any]:
        """Attempt to correct a failed SQL query and return just the corrected SQL."""
        try:
            correction_result = self.gemini_client.correct_failed_query(
                user_query, failed_sql, error_message, schema_description, faiss_summary
            )
            
            if not correction_result["success"]:
                return {"success": False, "error": correction_result["error"]}
            
            # Extract the corrected SQL directly from the raw response
            corrected_sql = correction_result.get("raw_response", "").strip()
            
            if not corrected_sql:
                return {"success": False, "error": "Empty SQL response from correction"}
            
            return {
                "success": True,
                "corrected_sql": corrected_sql
            }
                
        except Exception as e:
            logger.error(f"Query correction failed: {e}")
            return {"success": False, "error": str(e)}

#     def _refine_query_for_validation(self, user_query: str, sql_query: str,
#                                     execution_result: Dict[str, Any], validation_result: Dict[str, Any],
#                                     schema_description: str, faiss_summary: str) -> Dict[str, Any]:
#         """Refine a query that executes but doesn't produce correct results."""
#         try:
#             # Create a refinement prompt based on validation feedback
#             refinement_prompt = f"""
# The SQL query executed successfully but the results don't match the user's intent.

# User Query: {user_query}
# SQL Query: {sql_query}
# Query Results: {execution_result}
# Validation Feedback: {validation_result.get('reason', 'No specific feedback')}
# Suggestions: {validation_result.get('suggestions', 'No suggestions provided')}

# Please generate a refined SQL query that addresses the validation issues.
# """
            
#             # For now, we'll use the correction method as a fallback
#             # In a full implementation, you might want a dedicated refinement method
#             return self._correct_failed_query(
#                 user_query, sql_query, f"Validation failed: {validation_result.get('reason', 'Unknown')}",
#                 schema_description, faiss_summary
#             )
            
#         except Exception as e:
#             logger.error(f"❌ Query refinement failed: {e}")
#             return {"success": False, "error": str(e)}
    
    def _cleanup_workflow_results(self, workflow_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean up workflow results to ensure JSON serialization.
        Removes any DataFrames or non-serializable objects and converts dates.
        """
        try:
            import datetime
            
            def make_serializable(obj):
                """Recursively make objects JSON serializable."""
                if isinstance(obj, (datetime.date, datetime.datetime)):
                    return obj.isoformat()
                elif isinstance(obj, dict):
                    return {k: make_serializable(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [make_serializable(item) for item in obj]
                elif hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
                    # Handle pandas DataFrame or similar objects
                    return obj.to_dict(orient="records")
                else:
                    return obj
            
            cleaned_results = make_serializable(workflow_results)
            
            # Additional cleanup for specific known problematic objects
            if "steps" in cleaned_results:
                for step in cleaned_results["steps"]:
                    if isinstance(step, dict):
                        # Remove execution_result if it contains DataFrame
                        if "execution_result" in step:
                            execution_result = step["execution_result"]
                            if isinstance(execution_result, dict) and "df" in execution_result:
                                # Create a clean copy without DataFrame
                                clean_execution_result = execution_result.copy()
                                if "df" in clean_execution_result:
                                    clean_execution_result["results"] = clean_execution_result["df"].to_dict(orient="records")
                                    del clean_execution_result["df"]
                                step["execution_result"] = clean_execution_result
                        
                        # Remove any other potential DataFrame references
                        if "df" in step:
                            del step["df"]
            
            return cleaned_results
            
        except Exception as e:
            logger.warning(f"Workflow results cleanup failed: {e}")
            # Fallback: convert problematic objects to strings
            try:
                def stringify_problematic(obj):
                    if isinstance(obj, (datetime.date, datetime.datetime)):
                        return obj.isoformat()
                    elif isinstance(obj, dict):
                        return {k: stringify_problematic(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [stringify_problematic(item) for item in obj]
                    else:
                        try:
                            json.dumps(obj)
                            return obj
                        except (TypeError, ValueError):
                            return str(obj)
                
                return stringify_problematic(workflow_results)
            except Exception as fallback_error:
                logger.error(f"Even fallback cleanup failed: {fallback_error}")
                return workflow_results

    def _create_error_result(self, workflow_results: Dict[str, Any], error_type: str, error_message: str) -> Dict[str, Any]:
        """Create a standardized error result."""
        error_result = {
            "step": f"error_{error_type.lower().replace(' ', '_')}",
            "success": False,
            "error": error_message,
            "timestamp": time.time()
        }
        workflow_results["steps"].append(error_result)
        workflow_results["final_result"] = error_result
        workflow_results["success"] = False
        return workflow_results

    def cleanup(self):
        """Clean up all components."""
        try:
            self.query_tester.cleanup()
            logger.info("✅ Query Orchestrator cleanup completed")
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")

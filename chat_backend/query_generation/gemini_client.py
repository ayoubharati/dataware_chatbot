"""
Gemini Client for the Query Generation system.
Handles all interactions with the Gemini API for SQL generation and correction.
"""

import logging
import time
import google.generativeai as genai
import json
from typing import Dict, Any, Optional, List
from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_CONFIG, RETRY_TEMPERATURE
from prompt_templates import (
    INITIAL_RESOLVABILITY_PROMPT,
    INITIAL_QUERY_PROMPT,
    QUERY_CORRECTION_PROMPT,
    QUERY_VALIDATION_PROMPT,
    FINAL_RESPONSE_PROMPT
)
import re

logger = logging.getLogger(__name__)

class GeminiClient:
    """Handles all interactions with the Gemini API for SQL generation, correction, validation, and chart generation."""

    def __init__(self):
        """Initialize the Gemini client."""
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel(GEMINI_MODEL)
            logger.info("✅ Gemini client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini client: {e}")
            raise

    def check_initial_resolvability(self, user_query: str, schema_description: str, faiss_summary: str) -> Dict[str, Any]:
        try:
            prompt = self._build_initial_resolvability_prompt(user_query, schema_description, faiss_summary)
            
            logger.info("🔍 Checking initial resolvability with Gemini...")
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=200,
                    temperature=0.1,
                    top_p=0.9
                )
            )
            
            response_text = response.text.strip()
            logger.info(f"✅ Initial resolvability check completed")
            
            # Parse the structured response
            parsed = self._parse_resolvability_response(response_text)
            
            return {
                "success": True,
                "resolvable": parsed.get("resolvable", "no"),
                "message": parsed.get("message", "Unable to determine resolvability"),
                "reasoning": parsed.get("reasoning", ""),
                "raw_response": response_text,
                "prompt": prompt,
                "gemini_response": response_text,
                "parsed_response": parsed
            }
            
        except Exception as e:
            logger.error(f"❌ Initial resolvability check failed: {e}")
            return {
                "success": False,
                "resolvable": "no",
                "message": f"Error checking resolvability: {str(e)}",
                "reasoning": "",
                "raw_response": "",
                "prompt": "",
                "gemini_response": "",
                "parsed_response": {},
                "error": str(e)
            }

    def generate_initial_query(self, user_query: str, schema_description: str, faiss_summary: str) -> Dict[str, Any]:
        """Generate initial SQL query using Gemini."""
        try:
            prompt = self._build_initial_query_prompt(user_query, schema_description, faiss_summary)
            
            logger.info("🤖 Generating initial SQL query with Gemini...")
            start_time = time.time()
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=GEMINI_CONFIG['max_output_tokens'],
                    temperature=GEMINI_CONFIG['temperature'],
                    top_p=GEMINI_CONFIG['top_p']
                )
            )
            
            generation_time = time.time() - start_time
            response_text = response.text.strip()
            
            logger.info(f"✅ Initial query generated in {generation_time:.3f}s")
            
            # Parse the response to get SQL query
            sql_query = self._parse_structured_response(response_text)
            
            if not sql_query:
                return {
                    "success": False,
                    "error": "Failed to parse Gemini response or empty SQL received",
                    "prompt": prompt,
                    "gemini_response": response_text
                }
            
            return {
                "success": True,
                "sql_query": sql_query,
                "generation_time": generation_time,
                "prompt": prompt,
                "gemini_response": response_text
            }
            
        except Exception as e:
            logger.error(f"❌ Initial query generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "prompt": "",
                "gemini_response": ""
            }


    def correct_failed_query(self, user_query: str, failed_sql: str, error_message: str,
                           schema_description: str, faiss_summary: str) -> Dict[str, Any]:
        """Attempt to correct a failed SQL query."""
        try:
            prompt = self._build_correction_prompt(user_query, failed_sql, error_message, 
                                                schema_description, faiss_summary)
            
            logger.info("🔧 Attempting to correct failed SQL query...")
            start_time = time.time()
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=GEMINI_CONFIG['max_output_tokens'],
                    temperature=RETRY_TEMPERATURE,
                    top_p=GEMINI_CONFIG['top_p']
                )
            )
            
            correction_time = time.time() - start_time
            response_text = response.text.strip()
            
            logger.info(f"✅ Query correction completed in {correction_time:.3f}s")
            
            # Parse the structured response
            parsed = self._parse_structured_response(response_text)
            
            return {
                "success": True,
                "parsed_response": parsed,
                "raw_response": response_text,
                "correction_time": correction_time
            }
            
        except Exception as e:
            logger.error(f"❌ Query correction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "parsed_response": {},
                "raw_response": "",
                "correction_time": 0
            }

    def validate_query_results(self, user_query: str, sql_query: str, execution_result: Dict[str, Any],
                             schema_description: str, faiss_summary: str) -> Dict[str, Any]:
        """Validate if query results match user intent."""
        try:
            prompt = self._build_validation_prompt(user_query, sql_query, execution_result, 
                                                schema_description, faiss_summary)
            
            logger.info("🔍 Validating query results with Gemini...")
            start_time = time.time()
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=400,
                    temperature=0.1,
                    top_p=0.9
                )
            )
            
            validation_time = time.time() - start_time
            response_text = response.text.strip()
            
            logger.info(f"✅ Query validation completed in {validation_time:.3f}s")
            
            # Parse the validation response
            parsed = self._parse_validation_response(response_text)
            
            return {
                "success": True,
                "valid": parsed.get("valid", False),
                "reason": parsed.get("reason", "No reason provided"),
                "suggestions": parsed.get("suggestions", []),
                "raw_response": response_text,
                "validation_time": validation_time
            }
            
        except Exception as e:
            logger.error(f"❌ Query validation failed: {e}")
            return {
                "success": False,
                "valid": False,
                "reason": f"Validation failed: {str(e)}",
                "suggestions": [],
                "raw_response": "",
                "validation_time": 0
            }

    def generate_final_response_and_chart(self, user_query: str, final_sql: str, 
                                        query_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        
        try:
            prompt = self._build_final_response_prompt(user_query, final_sql, query_results)
            
            logger.info("🎨 Generating final response and chart with Gemini...")
            start_time = time.time()
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=800,
                    temperature=0.2,
                    top_p=0.9
                )
            )
            
            generation_time = time.time() - start_time
            response_text = response.text.strip()
            
            logger.info(f"✅ Final response and chart generation completed in {generation_time:.3f}s")
            
            # Parse the final response
            parsed = self._parse_final_response(response_text)
            
            return {
                "success": True,
                "parsed_response": parsed,
                "raw_response": response_text,
                "generation_time": generation_time
            }
            
        except Exception as e:
            logger.error(f"❌ Final response and chart generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "parsed_response": {},
                "raw_response": "",
                "generation_time": 0
            }

    def _build_initial_resolvability_prompt(self, user_query: str, schema_description: str, 
                                          faiss_summary: str) -> str:
        """Build prompt for initial resolvability check."""
        return INITIAL_RESOLVABILITY_PROMPT.format(
            user_query=user_query,
            schema_description=schema_description,
            faiss_summary=faiss_summary
        )

    def _build_initial_query_prompt(self, user_query: str, schema_description: str, faiss_summary: str) -> str:
        """Build prompt for initial SQL query generation."""
        return INITIAL_QUERY_PROMPT.format(
            user_query=user_query,
            schema_description=schema_description,
            faiss_summary=faiss_summary
        )

    def _build_correction_prompt(self, user_query: str, failed_sql: str, error_message: str,
                                schema_description: str, faiss_summary: str) -> str:
        """Build prompt for correcting failed SQL queries."""
        return QUERY_CORRECTION_PROMPT.format(
            user_query=user_query,
            failed_sql=failed_sql,
            error_message=error_message,
            schema_description=schema_description,
            faiss_summary=faiss_summary
        )

    def _build_validation_prompt(self, user_query: str, sql_query: str, execution_result: Dict[str, Any],
                                schema_description: str, faiss_summary: str) -> str:
        """Build prompt for validating query results."""
        limited_results = execution_result[:100] if isinstance(execution_result, list) else execution_result

        return QUERY_VALIDATION_PROMPT.format(
            user_query=user_query,
            sql_query=sql_query,
            query_results=json.dumps(limited_results, indent=2),
            schema_description=schema_description,
            faiss_summary=faiss_summary
        )

    def _build_final_response_prompt(self, user_query: str, final_sql: str, 
                               query_results: List[Dict[str, Any]]) -> str:
        """Build prompt for final response and chart generation."""
        # Ensure we handle date serialization properly
        try:
            # Import datetime if not already imported
            import datetime
            
            # Convert date objects to strings for JSON serialization
            def default_serializer(obj):
                if isinstance(obj, (datetime.date, datetime.datetime)):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
            
            limited_results = query_results[:100] if query_results else []
            serialized_results = json.dumps(limited_results, indent=2, default=default_serializer)
            
            return FINAL_RESPONSE_PROMPT.format(
                user_query=user_query,
                sql_query=final_sql,
                query_results=serialized_results,
            )
        except Exception as e:
            logger.error(f"Error building final response prompt: {e}")
            # Fallback without results if serialization fails
            return FINAL_RESPONSE_PROMPT.format(
                user_query=user_query,
                sql_query=final_sql,
                query_results="[]",
            )







    def _parse_resolvability_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the resolvability check response."""
        try:
            lines = response_text.strip().split('\n')
            result = {
                "resolvable": "no",
                "message": "",
                "reasoning": ""
            }
            
            for line in lines:
                line = line.strip()
                if line.startswith('RESOLVABLE:'):
                    result["resolvable"] = line.split(':', 1)[1].strip().lower()
                elif line.startswith('MESSAGE:'):
                    result["message"] = line.split(':', 1)[1].strip()
                elif line.startswith('REASONING:'):
                    result["reasoning"] = line.split(':', 1)[1].strip()
            
            return result
        except Exception as e:
            logger.error(f"Failed to parse resolvability response: {e}")
            return {"resolvable": "no", "message": "Parse error", "reasoning": ""}

    def _parse_structured_response(self, response_text: str) -> str:
        """Parse the SQL generation response - returns only the SQL query."""
        try:
            # Clean the response text
            sql_query = response_text.strip()
            
            # Handle case where response starts with "SQL:"
            if sql_query.upper().startswith('SQL:'):
                sql_query = sql_query[4:].strip()
            
            # Remove any markdown code blocks if present
            if sql_query.startswith('```sql'):
                sql_query = sql_query[6:]
            elif sql_query.startswith('```'):
                sql_query = sql_query[3:]
            
            if sql_query.endswith('```'):
                sql_query = sql_query[:-3]
            
            # Clean up any remaining whitespace
            sql_query = sql_query.strip()
            
            return sql_query
            
        except Exception as e:
            logger.error(f"Failed to parse SQL response: {e}")
            return ""

    def _parse_validation_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the validation response."""
        try:
            lines = response_text.strip().split('\n')
            result = {
                "valid": False,
                "reason": "",
                "suggestions": ""
            }
            
            for line in lines:
                line = line.strip()
                if line.startswith('VALID:'):
                    result["valid"] = line.split(':', 1)[1].strip().lower() == 'yes'
                elif line.startswith('REASON:'):
                    result["reason"] = line.split(':', 1)[1].strip()
                elif line.startswith('SUGGESTIONS:'):
                    # Keep suggestions as a simple string
                    result["suggestions"] = line.split(':', 1)[1].strip()
            
            return result
        except Exception as e:
            logger.error(f"Failed to parse validation response: {e}")
            return {"valid": False, "reason": "Parse error", "suggestions": ""}

   
    def _parse_final_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the final response and chart generation response."""
        try:
            lines = response_text.strip().split('\n')
            result = {
                "result_type": "",
                "chart_type": "",
                "message": ""
            }
            
            for line in lines:
                line = line.strip()
                if line.startswith('RESULT_TYPE:'):
                    result["result_type"] = line.split(':', 1)[1].strip().lower()
                elif line.startswith('CHART_TYPE:'):
                    chart_type_value = line.split(':', 1)[1].strip()
                    # Handle N/A case
                    if chart_type_value.upper() == 'N/A':
                        result["chart_type"] = None
                    else:
                        result["chart_type"] = chart_type_value.lower()
                elif line.startswith('MESSAGE:'):
                    result["message"] = line.split(':', 1)[1].strip()
            
            return result
        except Exception as e:
            logger.error(f"Failed to parse final response: {e}")
            return {
                "result_type": "text",
                "chart_type": None,
                "message": "Error parsing final response"
            }

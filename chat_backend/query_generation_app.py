#!/usr/bin/env python3
"""
Query Generation Flask App

This is a separate Flask application that provides routes for the new
modular query generation system. It runs alongside the existing app.py
but provides enhanced query processing capabilities.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import logging
import sys
import os
from typing import Dict, Any

# Add query_generation directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "query_generation"))

# Import our query generation system
from query_generation.query_orchestrator import QueryOrchestrator
from query_generation.smart_response_generator import SmartResponseGenerator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

# Global orchestrator instance
_orchestrator = None

def get_orchestrator():
    """Get or initialize the global query orchestrator (singleton pattern)"""
    global _orchestrator
    if _orchestrator is None:
        try:
            logger.info("🚀 Initializing Query Generation Orchestrator...")
            _orchestrator = QueryOrchestrator()
            logger.info("✅ Query Generation Orchestrator ready!")
        except Exception as e:
            logger.error(f"❌ Orchestrator initialization failed: {e}")
            return None
    return _orchestrator

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for query generation service"""
    return jsonify({
        'status': 'healthy',
        'service': 'Query Generation System',
        'message': 'Advanced query generation service is running',
        'timestamp': time.time()
    })

@app.route('/query/advanced', methods=['POST'])
def advanced_query():
    """
    Advanced query endpoint using the new 7-step workflow
    
    Expected JSON payload:
    {
        "query": "Make a bar chart of customer registrations in Australia by year",
        "options": {
            "max_retries": 3,
            "chart_preference": "auto" // Note: Currently not used by orchestrator
        }
    }
    
    Returns:
    {
        "success": true/false,
        "resolvable": true/false,
        "result_type": "chart" | "table" | "summary" | "text",
        "query": "SQL query string",
        "chart_data": "Plotly JSON" | null,  # Changed from Chart.js to Plotly
        "result": "data" | null,
        "message": "User-friendly message",
        "workflow_steps": [...],
        "execution_time": 1.234
    }
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing query in request body',
                'message': 'Please provide a query in the request body'
            }), 400
        
        user_query = data['query'].strip()
        
        if not user_query:
            return jsonify({
                'success': False,
                'error': 'Empty query provided',
                'message': 'Please provide a non-empty query'
            }), 400
        
        # Get options
        options = data.get('options', {})
        max_retries = options.get('max_retries', 3)
        chart_preference = options.get('chart_preference', 'auto')  # Currently unused
        
        logger.info(f"Processing advanced query: {user_query}")
        logger.info(f"   Options: max_retries={max_retries}, chart_preference={chart_preference}")
        
        # Get orchestrator
        orchestrator = get_orchestrator()
        if not orchestrator:
            return jsonify({
                'success': False,
                'error': 'Service unavailable',
                'message': 'Query generation service is not available'
            }), 503
        
        # Process the query using our 7-step workflow with max_retries parameter
        start_time = time.time()
        
        try:
            # Pass max_retries parameter to the workflow
            workflow_result = orchestrator.generate_query_workflow(user_query, max_retries)
            execution_time = time.time() - start_time
            
            if workflow_result.get('success'):
                # Workflow completed successfully
                final_result = workflow_result.get('final_result', {})
                
                # Prepare response
                response = {
                    'success': True,
                    'resolvable': final_result.get('resolvable', False),
                    'result_type': final_result.get('result_type', 'unknown'),
                    'query': final_result.get('query', ''),
                    'chart_data': final_result.get('chart_data'),  # Now contains Plotly JSON
                    'result': final_result.get('result'),
                    'message': final_result.get('message', 'Query processed successfully'),
                    'workflow_steps': workflow_result.get('steps', []),
                    'execution_time': round(execution_time, 3)
                }
                
                logger.info(f"Advanced query completed successfully in {execution_time:.3f}s")
                logger.info(f"   Result type: {response['result_type']}")
                logger.info(f"   Resolvable: {response['resolvable']}")
                
                return jsonify(response)
                
            else:
                # Workflow failed
                error_msg = workflow_result.get('error', 'Unknown error')
                final_result = workflow_result.get('final_result', {})
                
                # Check if it's an unresolvable query (not an error)
                if isinstance(final_result, dict) and final_result.get('resolvable') is False:
                    logger.info(f"Query marked as unresolvable: {final_result.get('message', 'Unknown reason')}")
                    return jsonify({
                        'success': True,  # Request was successful, query just isn't resolvable
                        'resolvable': False,
                        'result_type': None,
                        'query': '',
                        'chart_data': None,
                        'result': None,
                        'message': final_result.get('message', 'This query cannot be resolved with the available data'),
                        'reasoning': final_result.get('reasoning', ''),
                        'execution_time': round(execution_time, 3)
                    })
                else:
                    # Actual workflow error
                    logger.error(f"Advanced query workflow failed: {error_msg}")
                    return jsonify({
                        'success': False,
                        'error': 'Workflow failed',
                        'message': f'Query processing failed: {error_msg}',
                        'execution_time': round(execution_time, 3)
                    }), 500
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Advanced query processing error: {e}")
            
            return jsonify({
                'success': False,
                'error': 'Processing error',
                'message': f'An error occurred while processing your query: {str(e)}',
                'execution_time': round(execution_time, 3)
            }), 500
            
    except Exception as e:
        logger.error(f"Advanced query endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': 'Endpoint error',
            'message': f'Server error: {str(e)}'
        }), 500

@app.route('/query/cleanup', methods=['POST'])
def cleanup():
    """Cleanup endpoint to reset the system"""
    try:
        global _orchestrator
        
        if _orchestrator:
            _orchestrator.cleanup()
            _orchestrator = None
            logger.info("🧹 Query generation system cleaned up")
        
        return jsonify({
            'success': True,
            'message': 'System cleaned up successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Cleanup error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'message': 'The requested endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An internal server error occurred'
    }), 500

if __name__ == '__main__':
    logger.info("🚀 Starting Query Generation Flask App...")
    logger.info("   Available endpoints:")
    logger.info("   - GET  /health")
    logger.info("   - POST /query/advanced")
    logger.info("   - GET  /query/status")
    logger.info("   - POST /query/test")
    logger.info("   - POST /query/cleanup")
    
    # Run on different port to avoid conflict with main app.py
    app.run(host='0.0.0.0', port=5001, debug=True)

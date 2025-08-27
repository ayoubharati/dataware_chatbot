"""
Configuration file for the Query Generation system.
Contains all the necessary configuration parameters and database settings.
"""

import os
from typing import Dict, Any

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'dataware_test',
    'user': 'postgres',
    'password': 'bath123'
}

# Gemini Configuration
GEMINI_API_KEY = "AIzaSyBpzfYE3-shtUotP7iCBs34MNleO5upsrU"
GEMINI_MODEL = 'gemini-1.5-flash'

# File Paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMA_FILE_PATH = os.path.join(BASE_DIR, "schema_dataware_test.md")

# FAISS Configuration
FAISS_PER_TERM_K = 10
FAISS_WHOLE_QUERY_K = 10

# Gemini Generation Config
GEMINI_CONFIG = {
    'max_output_tokens': 800,
    'temperature': 0.2,
    'top_p': 0.9
}

# Retry Configuration
MAX_RETRY_ATTEMPTS = 3
RETRY_TEMPERATURE = 0.1

# Logging Configuration
DEBUG_LOG_DIR = os.path.join(BASE_DIR, "debug_logs")
QUERY_LOG_DIR = os.path.join(DEBUG_LOG_DIR, "query_generation")

# Ensure log directories exist
os.makedirs(DEBUG_LOG_DIR, exist_ok=True)
os.makedirs(QUERY_LOG_DIR, exist_ok=True)

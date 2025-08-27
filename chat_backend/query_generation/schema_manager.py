"""
Schema Manager for the Query Generation system.
Loads the existing database schema from schema_dataware_test.md.
"""

import os
import logging
from typing import Optional, Dict, Any
from config import SCHEMA_FILE_PATH

logger = logging.getLogger(__name__)

class SchemaManager:
    """Manages database schema loading from existing schema file."""
    
    def __init__(self):
        self.schema_content = ""
        logger.info("✅ SchemaManager initialized")
    
    def load_schema(self) -> str:
        """Load the database schema from existing schema_dataware_test.md."""
        try:
            if os.path.exists(SCHEMA_FILE_PATH):
                with open(SCHEMA_FILE_PATH, 'r', encoding='utf-8') as f:
                    self.schema_content = f.read()
                logger.info(f"✅ Schema loaded from {SCHEMA_FILE_PATH}")
                return self.schema_content
            else:
                logger.error(f"❌ Schema file not found: {SCHEMA_FILE_PATH}")
                return ""
        except Exception as e:
            logger.error(f"❌ Failed to load schema: {e}")
            return ""
    
    def get_combined_schema_description(self) -> str:
        """Get the schema description (just the schema file content)."""
        schema = self.load_schema()
        if not schema:
            logger.error("❌ No schema content available")
            return ""
        
        return schema
    
    def get_schema_content(self) -> str:
        """Get the raw schema content."""
        return self.schema_content

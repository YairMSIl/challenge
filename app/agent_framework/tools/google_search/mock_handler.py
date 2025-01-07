"""Google Search Mock Handler
========================

Handles mock responses for Google Search API calls.

Public Components:
- MockHandler: Class for managing mock responses

Design Decisions:
- Uses file-based storage for mock data
- Implements timestamp-based versioning
- Provides automatic cleanup of old mocks
- Maintains mock directory structure
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from ..tool_constants import ToolConfig
from ..tools_utils import ensure_directory, str_to_bool
from utils.logging_config import get_logger

logger = get_logger(__name__)

class MockHandler:
    """Handler for Google Search mock responses."""
    
    def __init__(self):
        """Initialize the mock handler."""
        self.mock_dir = Path(ToolConfig.MOCK_DIR)
        ensure_directory(self.mock_dir)
        
    def save_response(self, response_content: Any) -> None:
        """
        Save API response for mock testing.
        
        Args:
            response_content: The API response to save
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.mock_dir / f"google_search_{timestamp}.json"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(response_content, f, indent=2)
                
            logger.debug(f"Saved mock response to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save mock response: {str(e)}")
            
    def get_latest_response(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent mock response if available.
        
        Returns:
            Mock response data if available, None otherwise
        """
        try:
            if not self.mock_dir.exists():
                return None
                
            # Get all google search response files
            mock_files = list(self.mock_dir.glob("google_search_*.json"))
            if not mock_files:
                return None
                
            # Get most recent file
            latest_mock = max(mock_files, key=lambda p: p.stat().st_mtime)
            logger.debug(f"Found mock response file: {latest_mock}")
            
            with open(latest_mock, 'r', encoding='utf-8') as f:
                mock_data = json.load(f)
                
            logger.info("Using mock response instead of making API call")
            return mock_data
            
        except Exception as e:
            logger.error(f"Failed to load mock response: {str(e)}")
            return None
 
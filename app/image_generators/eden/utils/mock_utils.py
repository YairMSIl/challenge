"""Eden AI Mock Utilities
===================

Utilities for handling mock responses in development/testing.

Design Decisions:
- Separates mock handling from main logic
- Provides consistent mock data structure
- Supports saving and loading mock responses
- Uses timestamps for mock file naming
"""

import json
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from ..exceptions.eden_exceptions import MockError
from ..config.constants import MOCK_DIR, MOCK_RESPONSE_PREFIX, MOCK_RESPONSE_SUFFIX

def save_mock_response(response_content: Dict[str, Any]) -> None:
    """
    Save API response for mock testing.
    
    Args:
        response_content: API response data to save
    """
    try:
        # Ensure mock directory exists
        MOCK_DIR.mkdir(parents=True, exist_ok=True)
        
        # Create timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = MOCK_DIR / f"{MOCK_RESPONSE_PREFIX}{timestamp}{MOCK_RESPONSE_SUFFIX}"
        
        # Save response
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(response_content, f, indent=2)
            
    except Exception as e:
        raise MockError(f"Failed to save mock response: {str(e)}")

def get_mock_response() -> Optional[Dict[str, Any]]:
    """
    Get the most recent mock response if available.
    
    Returns:
        Mock response data if available, None otherwise
    """
    try:
        if not MOCK_DIR.exists():
            return None
            
        # Get all mock response files
        mock_files = list(MOCK_DIR.glob(f"{MOCK_RESPONSE_PREFIX}*{MOCK_RESPONSE_SUFFIX}"))
        if not mock_files:
            return None
            
        # Get most recent file
        latest_mock = max(mock_files, key=lambda p: p.stat().st_mtime)
        
        # Load and return mock data
        with open(latest_mock, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    except Exception as e:
        raise MockError(f"Failed to load mock response: {str(e)}")

def should_use_mock(env_value: str) -> bool:
    """
    Determine if mock should be used based on environment value.
    
    Args:
        env_value: Environment variable value
        
    Returns:
        True if mock should be used, False otherwise
    """
    return env_value.lower() in ('true', 't', 'yes', 'y', '1', 'on') 
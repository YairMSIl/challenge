"""Mock Service for Audio Generation
==============================

Handles mock responses for testing and development.

Design Decisions:
- Separates mock functionality from main service
- Provides realistic mock responses
- Supports different mock types
- Maintains mock file structure
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from ..models.config import MockConfig
from ..models.exceptions import FileSystemError
from ..enums import MockType
from ..constants import (
    MOCK_CREATION_DIR, MOCK_RETRIEVAL_DIR,
    MOCK_FILE_PREFIX, MOCK_FILE_EXT,
    TIMESTAMP_FORMAT
)
from utils.logging_config import get_logger

logger = get_logger(__name__)

class MockService:
    """Service for handling mock responses."""
    
    def __init__(self, config: MockConfig):
        """Initialize mock service."""
        self.config = config
        self._setup_directories()
        
    def _setup_directories(self):
        """Create necessary mock directories."""
        try:
            MOCK_CREATION_DIR.mkdir(parents=True, exist_ok=True)
            MOCK_RETRIEVAL_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise FileSystemError(
                "Failed to create mock directories",
                str(MOCK_CREATION_DIR.parent),
                "mkdir"
            ) from e
            
    def _get_mock_path(self, mock_type: MockType) -> Path:
        """Get the appropriate mock directory for the given type."""
        return MOCK_CREATION_DIR if mock_type == MockType.CREATION else MOCK_RETRIEVAL_DIR
        
    def _get_timestamp(self) -> str:
        """Get current timestamp for file naming."""
        return datetime.now().strftime(TIMESTAMP_FORMAT)
        
    def save_response(
        self,
        response_data: Dict[str, Any],
        mock_type: MockType
    ) -> None:
        """
        Save API response for future mocking.
        
        Args:
            response_data: The API response to save
            mock_type: Type of mock response
        """
        if not self.config.save_responses:
            return
            
        try:
            mock_dir = self._get_mock_path(mock_type)
            timestamp = self._get_timestamp()
            mock_file = mock_dir / f"{MOCK_FILE_PREFIX}_{timestamp}{MOCK_FILE_EXT}"
            
            logger.debug(f"Saving {mock_type.value} mock response to {mock_file}")
            
            with open(mock_file, 'w') as f:
                json.dump(response_data, f, indent=2)
                
            logger.debug(f"Successfully saved mock response to {mock_file}")
            
        except Exception as e:
            logger.error(f"Failed to save mock response: {str(e)}")
            raise FileSystemError(
                "Failed to save mock response",
                str(mock_file),
                "write"
            ) from e
            
    def get_response(self, mock_type: MockType) -> Optional[Dict[str, Any]]:
        """
        Get most recent mock response of given type.
        
        Args:
            mock_type: Type of mock to retrieve
            
        Returns:
            Mock response data if available, None otherwise
        """
        if not self.config.enabled:
            return None
            
        try:
            mock_dir = self._get_mock_path(mock_type)
            mock_files = list(mock_dir.glob(f"{MOCK_FILE_PREFIX}*{MOCK_FILE_EXT}"))
            
            if not mock_files:
                logger.debug(f"No mock responses found for type {mock_type.value}")
                return None
                
            latest_mock = max(mock_files, key=lambda p: p.stat().st_mtime)
            logger.debug(f"Found mock response file: {latest_mock}")
            
            with open(latest_mock, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Failed to load mock response: {str(e)}")
            raise FileSystemError(
                "Failed to load mock response",
                str(mock_dir),
                "read"
            ) from e 
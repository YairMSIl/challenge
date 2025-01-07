"""Storage Service for Audio Generation
================================

Handles file storage operations for generated audio files.

Design Decisions:
- Separates storage concerns from main service
- Implements proper error handling
- Uses pathlib for cross-platform compatibility
- Maintains consistent file naming
"""

from pathlib import Path
from typing import Optional
from datetime import datetime

from ..models.exceptions import FileSystemError
from ..constants import (
    AUDIO_DIR, AUDIO_FILE_PREFIX,
    AUDIO_FILE_EXT, TIMESTAMP_FORMAT
)
from utils.logging_config import get_logger

logger = get_logger(__name__)

class StorageService:
    """Service for handling file storage operations."""
    
    def __init__(self):
        """Initialize storage service."""
        self._setup_directories()
        
    def _setup_directories(self):
        """Create necessary storage directories."""
        try:
            AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise FileSystemError(
                "Failed to create audio directory",
                str(AUDIO_DIR),
                "mkdir"
            ) from e
            
    def _get_timestamp(self) -> str:
        """Get current timestamp for file naming."""
        return datetime.now().strftime(TIMESTAMP_FORMAT)
        
    def save_audio(self, audio_data: bytes) -> Path:
        """
        Save audio data to file.
        
        Args:
            audio_data: Raw audio data to save
            
        Returns:
            Path to the saved audio file
        """
        try:
            timestamp = self._get_timestamp()
            audio_file = AUDIO_DIR / f"{AUDIO_FILE_PREFIX}_{timestamp}{AUDIO_FILE_EXT}"
            
            logger.debug(f"Saving audio to {audio_file}")
            
            with open(audio_file, 'wb') as f:
                f.write(audio_data)
                
            logger.debug(f"Successfully saved audio to {audio_file}")
            return audio_file
            
        except Exception as e:
            logger.error(f"Failed to save audio file: {str(e)}")
            raise FileSystemError(
                "Failed to save audio file",
                str(audio_file),
                "write"
            ) from e
            
    def get_audio_path(self, filename: str) -> Optional[Path]:
        """
        Get path to an existing audio file.
        
        Args:
            filename: Name of the audio file
            
        Returns:
            Path to the audio file if it exists, None otherwise
        """
        try:
            audio_file = AUDIO_DIR / filename
            return audio_file if audio_file.exists() else None
            
        except Exception as e:
            logger.error(f"Failed to get audio file path: {str(e)}")
            raise FileSystemError(
                "Failed to get audio file path",
                str(AUDIO_DIR),
                "read"
            ) from e
            
    def delete_audio(self, filename: str) -> bool:
        """
        Delete an audio file.
        
        Args:
            filename: Name of the audio file to delete
            
        Returns:
            True if file was deleted, False if it didn't exist
        """
        try:
            audio_file = AUDIO_DIR / filename
            if audio_file.exists():
                audio_file.unlink()
                logger.debug(f"Deleted audio file: {audio_file}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete audio file: {str(e)}")
            raise FileSystemError(
                "Failed to delete audio file",
                str(audio_file),
                "delete"
            ) from e 
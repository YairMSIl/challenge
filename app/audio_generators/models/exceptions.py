"""Exceptions for Audio Generation Service
===================================

Contains all custom exceptions used in the audio generation service.

Design Decisions:
- Implements hierarchy of exceptions
- Provides detailed error messages
- Includes error context where applicable
- Supports proper error handling patterns
"""

from typing import Optional, Dict, Any
from ..enums import ErrorType

class AudioGenerationError(Exception):
    """Base exception for all audio generation errors."""
    
    def __init__(
        self,
        message: str,
        error_type: ErrorType = ErrorType.UNKNOWN,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        super().__init__(self.message)

class APIError(AudioGenerationError):
    """Raised when API request fails."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        details = {
            'status_code': status_code,
            'response_data': response_data
        }
        super().__init__(message, ErrorType.API, details)

class ValidationError(AudioGenerationError):
    """Raised when validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        details = {'field': field} if field else {}
        super().__init__(message, ErrorType.VALIDATION, details)

class NetworkError(AudioGenerationError):
    """Raised when network operations fail."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        details = {'original_error': str(original_error)} if original_error else {}
        super().__init__(message, ErrorType.NETWORK, details)

class FileSystemError(AudioGenerationError):
    """Raised when file operations fail."""
    
    def __init__(
        self,
        message: str,
        path: Optional[str] = None,
        operation: Optional[str] = None
    ):
        details = {
            'path': path,
            'operation': operation
        }
        super().__init__(message, ErrorType.FILE_SYSTEM, details) 
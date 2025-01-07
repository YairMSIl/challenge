"""Eden AI Exceptions
=================

Custom exceptions for the Eden AI image generation module.

Design Decisions:
- Specific exception types for different error cases
- Includes context in error messages
- Supports error details for debugging
"""

from typing import Optional, Dict, Any

class EdenAIError(Exception):
    """Base exception for Eden AI errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class ConfigurationError(EdenAIError):
    """Raised when there are configuration issues."""
    pass

class APIError(EdenAIError):
    """Raised when the API returns an error."""
    pass

class ImageSaveError(EdenAIError):
    """Raised when there are issues saving images."""
    pass

class MockError(EdenAIError):
    """Raised when there are issues with mock operations."""
    pass

class ValidationError(EdenAIError):
    """Raised when input validation fails."""
    pass 
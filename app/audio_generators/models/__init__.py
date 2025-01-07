"""Models Package for Audio Generation
==============================

Contains all data models used in the audio generation service.

Public Components:
- AudioGenerationConfig: Configuration dataclass
- GenerationResponse: API response model
- AudioGenerationError: Base exception class

Design Decisions:
- Uses dataclasses for clean data handling
- Implements proper validation
- Provides helper methods
"""

from .config import AudioGenerationConfig, MockConfig
from .response import GenerationResponse, AudioFile, APIError
from .exceptions import (
    AudioGenerationError,
    ValidationError,
    NetworkError,
    FileSystemError
)

__all__ = [
    'AudioGenerationConfig',
    'MockConfig',
    'GenerationResponse',
    'AudioFile',
    'APIError',
    'AudioGenerationError',
    'ValidationError',
    'NetworkError',
    'FileSystemError'
] 
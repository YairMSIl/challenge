"""Enums for Audio Generation Service
================================

Contains all enumerated types used across the audio generation service.

Design Decisions:
- Uses Python's Enum class for type safety
- Provides descriptive names and values
- Groups related enums together
"""

from enum import Enum, auto

class MockType(Enum):
    """Types of mock responses."""
    CREATION = "creation"
    RETRIEVAL = "retrieval"

class GenerationStatus(Enum):
    """Status of audio generation jobs."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    GENERATION = "generating"

class ErrorType(Enum):
    """Types of errors that can occur during audio generation."""
    NETWORK = auto()
    API = auto()
    VALIDATION = auto()
    FILE_SYSTEM = auto()
    UNKNOWN = auto()

class AudioFormat(Enum):
    """Supported audio formats."""
    WAV = ".wav"
    MP3 = ".mp3"
    OGG = ".ogg" 
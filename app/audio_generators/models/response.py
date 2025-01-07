"""Response Models for Audio Generation
=================================

Contains all response related models used in the audio generation service.

Design Decisions:
- Uses dataclasses for clean response handling
- Implements proper validation
- Provides helper methods for common operations
- Uses type hints for better IDE support
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path
from ..enums import GenerationStatus, ErrorType

@dataclass
class AudioFile:
    """Represents an audio file in the API response."""
    url: str
    content_type: str
    file_name: str
    file_size: int
    local_path: Optional[Path] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AudioFile':
        """Create AudioFile instance from API response dict."""
        return cls(
            url=data['url'],
            content_type=data['content_type'],
            file_name=data['file_name'],
            file_size=data['file_size']
        )

@dataclass
class APIError:
    """Represents an error in the API response."""
    message: str
    type: ErrorType
    details: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'APIError':
        """Create APIError instance from API response dict."""
        return cls(
            message=data.get('message', 'Unknown error'),
            type=ErrorType.API,
            details=data.get('details')
        )

@dataclass
class GenerationResponse:
    """Represents a complete generation response."""
    id: str
    status: GenerationStatus
    audio_file: Optional[AudioFile] = None
    error: Optional[APIError] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GenerationResponse':
        """Create GenerationResponse instance from API response dict."""
        response = cls(
            id=data['id'],
            status=GenerationStatus(data['status'])
        )
        
        if 'audio_file' in data:
            response.audio_file = AudioFile.from_dict(data['audio_file'])
            
        if 'error' in data:
            response.error = APIError.from_dict(data['error'])
            
        return response

    def is_complete(self) -> bool:
        """Check if generation is complete."""
        return self.status == GenerationStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if generation failed."""
        return self.status == GenerationStatus.FAILED 
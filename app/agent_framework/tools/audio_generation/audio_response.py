"""Audio Generation Response
=======================

Response classes for the Audio Generation Tool.

Public Components:
- AudioGenerationResponse: Response class for audio generation results

Design Decisions:
- Uses dataclasses for clean serialization
- Implements proper type hints
- Follows response pattern
"""

from dataclasses import dataclass
from typing import Optional
from ..tools_utils import BaseToolResponse, ToolResponseStatus

@dataclass
class AudioGenerationResponse(BaseToolResponse):
    """Response class for audio generation results."""
    audio_key: Optional[str] = None
    
    def to_string(self) -> str:
        """Convert response to JSON string."""
        response_dict = {
            "status": self.status.value,
            "message": self.message,
            "error": self.error,
            "audio_key": self.audio_key
        }
        return super().to_string() 
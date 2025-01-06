"""Image Generation Response
=======================

Response classes for the Image Generation Tool.

Public Components:
- ImageGenerationResponse: Response class for image generation results

Design Decisions:
- Uses dataclasses for clean serialization
- Implements proper type hints
- Follows response pattern
"""

from dataclasses import dataclass
from typing import Optional
from ..tools_utils import BaseToolResponse, ToolResponseStatus

@dataclass
class ImageGenerationResponse(BaseToolResponse):
    """Response class for image generation results."""
    image_key: Optional[str] = None
    
    def to_string(self) -> str:
        """Convert response to JSON string."""
        response_dict = {
            "status": self.status.value,
            "message": self.message,
            "error": self.error,
            "image_key": self.image_key
        }
        return super().to_string() 
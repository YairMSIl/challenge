"""Image Generation Tool Package
=========================

Tool for generating images using Eden AI service.

Public Components:
- ImageGenerationTool: Main tool class for generating images
- ImageGenerationResponse: Response class for generation results

Design Decisions:
- Splits functionality into focused modules
- Uses proper dependency injection
- Implements clean separation of concerns
"""

from .tool import ImageGenerationTool
from .image_response import ImageGenerationResponse

__all__ = ['ImageGenerationTool', 'ImageGenerationResponse'] 
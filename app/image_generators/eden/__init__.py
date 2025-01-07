"""Eden AI Image Generation Package
============================

Public interface for Eden AI image generation functionality.

Design Decisions:
- Exposes only necessary components
- Maintains clean public interface
- Provides type hints for better IDE support
"""

from .generator import EdenImageGenerator
from .models.image_models import ImageGenerationRequest, ImageGenerationResponse
from .exceptions.eden_exceptions import EdenAIError

__all__ = [
    'EdenImageGenerator',
    'ImageGenerationRequest',
    'ImageGenerationResponse',
    'EdenAIError'
] 
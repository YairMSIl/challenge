"""Eden AI Data Models
==================

Data models for Eden AI image generation requests and responses.

Design Decisions:
- Uses dataclasses for clean data structures
- Includes validation in model methods
- Separates request and response models
- Includes helper methods for common operations
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from ..config.constants import DEFAULT_PROVIDER, DEFAULT_MODEL, DEFAULT_RESOLUTION, DEFAULT_NUM_IMAGES, ResponseStatus

@dataclass
class ImageGenerationSettings:
    """Settings for image generation request."""
    provider: str = DEFAULT_PROVIDER
    model: str = DEFAULT_MODEL
    
    def to_dict(self) -> Dict[str, str]:
        """Convert settings to API-compatible dictionary."""
        return {self.provider: self.model}

@dataclass
class ImageGenerationRequest:
    """Request model for image generation."""
    text: str
    providers: str = DEFAULT_PROVIDER
    resolution: str = DEFAULT_RESOLUTION
    num_images: int = DEFAULT_NUM_IMAGES
    response_as_dict: bool = False
    settings: ImageGenerationSettings = field(default_factory=ImageGenerationSettings)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert request to API-compatible dictionary."""
        return {
            "providers": self.providers,
            "text": self.text,
            "resolution": self.resolution,
            "num_images": self.num_images,
            "response_as_dict": self.response_as_dict,
            "settings": self.settings.to_dict()
        }

@dataclass
class ImageGenerationError:
    """Error details from API response."""
    message: str
    details: Optional[Dict[str, Any]] = None

@dataclass
class GeneratedImage:
    """Details of a generated image."""
    image_data: str
    format: str
    cost: float = 0.0

@dataclass
class ImageGenerationResponse:
    """Response model for image generation."""
    status: ResponseStatus
    images: List[GeneratedImage] = field(default_factory=list)
    error: Optional[ImageGenerationError] = None
    debug_path: Optional[str] = None
    
    @property
    def is_success(self) -> bool:
        """Check if the generation was successful."""
        return self.status == ResponseStatus.SUCCESS
    
    @property
    def first_image(self) -> Optional[GeneratedImage]:
        """Get the first generated image if available."""
        return self.images[0] if self.images else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary format."""
        result = {
            "error": bool(self.error),
            "status": self.status.value
        }
        
        if self.error:
            result["message"] = self.error.message
        elif self.first_image:
            result["base64_image"] = self.first_image.image_data
            
        if self.debug_path:
            result["debug_path"] = self.debug_path
            
        return result 
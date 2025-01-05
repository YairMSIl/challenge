"""Eden AI Image Generation Tool
=========================

SmolAgents tool for generating images using Eden AI service.

Public Components:
- EdenImageGenerationTool: Tool class for image generation using Eden AI
- ImageGenerationResponse: Response class with serialization methods

Design Decisions:
- Uses session-based image storage for UI display
- Generates unique keys for each image
- Integrates with cost tracking system
- Supports mock responses for testing
- Returns image path in response dict for UI rendering
- Handles session management internally
- Exposes simple prompt-only interface to LLM
- Uses proper serialization methods for responses
"""

import uuid
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from smolagents import Tool
from app.image_generators.eden_image import eden_image_generator
from app.models.artifact import Artifact, ArtifactType
from utils.logging_config import get_logger

# Get logger instance
logger = get_logger(__name__)

@dataclass
class ImageGenerationResponse:
    """Response class for image generation results."""
    success: bool
    image_key: str
    error: Optional[str] = None

    def to_string(self) -> str:
        """Convert response to JSON string."""
        return json.dumps({
            "success": self.success,
            "image_key": self.image_key,
            "error": self.error
        })

    @classmethod
    def from_json(cls, json_str: str) -> 'ImageGenerationResponse':
        """Create response object from JSON string."""
        data = json.loads(json_str)
        return cls(
            success=data["success"],
            image_key=data["image_key"],
            error=data.get("error")
        )

class EdenImageGenerationTool(Tool):
    """Tool for generating images using Eden AI."""
    
    name = "generate_image"
    description = """
    This tool generates images based on text descriptions using Eden AI.
    It returns a JSON string containing either the generated image key or an error message.
    """
    inputs = {
        "prompt": {
            "type": "string",
            "description": "Text description of the image to generate",
        }
    }
    output_type = "string"  # Returns JSON string
    
    def __init__(self, session_id: str, artifacts: List):
        """Initialize the image generation tool."""
        super().__init__()
        self.set_session_id(session_id)
        self.artifacts = artifacts
        
    def set_session_id(self, session_id: str) -> None:
        """Set the current session ID for the tool."""
        self.current_session_id = session_id
        
    def forward(self, prompt: str) -> str:
        """
        Generate an image based on a text description.
        
        Args:
            prompt: Text description of the image to generate
            
        Returns:
            JSON string containing:
                success: Boolean indicating if generation was successful
                image_key: Unique key to access the generated image
                error: Optional error message if generation failed
        """
        try:
            if not self.current_session_id:
                logger.error("No session ID set for image generation")
                return ImageGenerationResponse(
                    success=False,
                    image_key="",
                    error="Internal error: No session ID available"
                ).to_string()
            
            logger.info(f"Generating image for prompt: {prompt[:50]}...")
            
            # Use default options for simplicity
            result = eden_image_generator.generate_image(
                prompt=prompt,
                session_id=self.current_session_id,
                options={"resolution": "256x256"}  # Fixed default options
            )
            
            if result.get("error"):
                logger.error(f"Image generation failed: {result['message']}")
                return ImageGenerationResponse(
                    success=False,
                    image_key="",
                    error=result["message"]
                ).to_string()
                
            # Generate unique key for this image
            image_key = f"{self.current_session_id}_{str(uuid.uuid4())}"
            
            # Store base64 image data
            self.artifacts.append(Artifact(
                is_new=True,
                content=result["base64_image"],
                type=ArtifactType.IMAGE
            ))
            
            logger.info(f"Image generated successfully with key: {image_key}")
            return ImageGenerationResponse(
                success=True,
                image_key=image_key,
                error=None
            ).to_string()
            
        except Exception as e:
            error_msg = f"Image generation failed: {str(e)}"
            logger.error(error_msg)
            return ImageGenerationResponse(
                success=False,
                image_key="",
                error=error_msg
            ).to_string()

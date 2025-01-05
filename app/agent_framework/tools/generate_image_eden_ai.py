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
    message: Optional[str] = None
    error: Optional[str] = None

    def to_string(self) -> str:
        """Convert response to JSON string."""
        return json.dumps({
            "success": self.success,
            "message": self.message,
            "error": self.error
        })

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
                error: Optional error message if generation failed
        """
        try:
            if not self.current_session_id:
                logger.error("No session ID set for image generation")
                return ImageGenerationResponse(
                    success=False,
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
                    error=result["message"]
                ).to_string()
                
            # Store base64 image data
            self.artifacts.append(Artifact(
                is_new=True,
                content=result["base64_image"],
                type=ArtifactType.IMAGE
            ))

            return ImageGenerationResponse(
                success=True,
                message="Image generated successfully. Please see artifacts.",
                error=None
            ).to_string()
            
        except Exception as e:
            error_msg = f"Image generation failed: {str(e)}"
            logger.error(error_msg)
            return ImageGenerationResponse(
                success=False,
                error=error_msg
            ).to_string()

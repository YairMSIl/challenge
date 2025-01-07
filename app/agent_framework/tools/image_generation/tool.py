"""Image Generation Tool Implementation
===============================

Main implementation of the Image Generation Tool.

Public Components:
- ImageGenerationTool: Tool class for generating images

Design Decisions:
- Uses Eden AI for image generation
- Implements proper error handling
- Provides base64 encoded images
- Follows tool interface pattern
"""

from typing import Optional, List, Dict, Any
from app.image_generators.eden import EdenImageGenerator
from app.models.artifact import ArtifactType
from ..tools_utils import BaseTool, ToolResponseStatus
from ..tool_constants import ToolName, ToolConfig, IMAGE_TOOL_INPUTS
from .image_response import ImageGenerationResponse
from utils.logging_config import get_logger

logger = get_logger(__name__)

class ImageGenerationTool(BaseTool):
    """Tool for generating images using Eden AI."""
    
    name = ToolName.IMAGE_GENERATOR.value
    description = """
    This tool generates images based on text descriptions using Eden AI.
    It returns a JSON string containing either the generated image key or an error message.
    """
    inputs = IMAGE_TOOL_INPUTS
    output_type = "string"  # Returns JSON string
    
    def __init__(self, session_id: Optional[str] = None, artifacts: Optional[List] = None):
        """
        Initialize the image generation tool.
        
        Args:
            session_id: Optional session ID for tracking artifacts
            artifacts: Optional list for storing generated artifacts
        """
        super().__init__(session_id, artifacts)
        self.eden_image_generator = EdenImageGenerator()
        logger.info("ImageGenerationTool initialized successfully")
        
    def forward(self, prompt: str) -> str:
        """
        Generate an image based on a text description.
        
        Args:
            prompt: Text description of the image to generate
            
        Returns:
            JSON string containing:
                status: Status of the generation (success/error)
                message: Success message if generation succeeded
                error: Optional error message if generation failed
                image_key: Key to access the generated image
        """
        try:
            if not self.artifact_handler.session_id:
                logger.error("No session ID set for image generation")
                return ImageGenerationResponse(
                    status=ToolResponseStatus.ERROR,
                    error="Internal error: No session ID available"
                ).to_string()
            
            logger.info(f"Generating image for prompt: {prompt[:50]}...")
            
            # Use default options for simplicity
            result = self.eden_image_generator.generate_image(
                prompt=prompt,
                session_id=self.artifact_handler.session_id,
                options={"resolution": ToolConfig.DEFAULT_IMAGE_RESOLUTION}
            )
            
            if result.get("error"):
                logger.error(f"Image generation failed: {result['message']}")
                return ImageGenerationResponse(
                    status=ToolResponseStatus.ERROR,
                    error=result["message"]
                ).to_string()
                
            # Store base64 image data
            self.artifact_handler.add_artifact(result["base64_image"], ArtifactType.IMAGE.value)
            
            return ImageGenerationResponse(
                status=ToolResponseStatus.SUCCESS,
                message="Image generated successfully. Note: The image is displayed in the UI for the user in the artifacts section.",
                image_key=result.get("image_key")
            ).to_string()
            
        except Exception as e:
            error_msg = f"Image generation failed: {str(e)}"
            logger.error(error_msg)
            return ImageGenerationResponse(
                status=ToolResponseStatus.ERROR,
                error=error_msg
            ).to_string() 
"""Audio Generation Tool Implementation
===============================

Main implementation of the Audio Generation Tool.

Design Decisions:
- Uses AIML API for audio generation
- Implements proper error handling
- Provides base64 encoded audio
- Follows tool interface pattern
"""

import base64
from pathlib import Path
from typing import Optional, List

from app.audio_generators import (
    AudioGenerator,
    AudioGenerationConfig,
    AudioGenerationError
)
from app.models.artifact import ArtifactType
from ..tools_utils import BaseTool, ToolResponseStatus
from ..tool_constants import ToolName, ToolConfig, AUDIO_TOOL_INPUTS
from .audio_response import AudioGenerationResponse
from utils.logging_config import get_logger

logger = get_logger(__name__)

class AudioGenerationTool(BaseTool):
    """Tool for generating audio using AIML API."""
    
    name = ToolName.AUDIO_GENERATOR.value
    description = """
    This tool generates audio content from text prompts using AIML API.
    It returns a JSON string containing the generation results or error message.
    """
    inputs = AUDIO_TOOL_INPUTS
    output_type = "string"  # Returns JSON string
    
    def __init__(self, session_id: Optional[str] = None, artifacts: Optional[List] = None):
        """
        Initialize the audio generator tool.
        
        Args:
            session_id: Optional session ID for tracking artifacts
            artifacts: Optional list for storing generated artifacts
        """
        super().__init__(session_id, artifacts)
        try:
            self.generator = AudioGenerator()
            logger.info("AudioGenerationTool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AudioGenerationTool: {str(e)}")
            raise
            
    def _encode_audio_file(self, audio_path: Path) -> str:
        """
        Convert audio file to base64 string.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Base64 encoded string of the audio file
        """
        try:
            with open(audio_path, 'rb') as audio_file:
                audio_bytes = audio_file.read()
                return base64.b64encode(audio_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encode audio file: {str(e)}")
            raise
            
    def forward(
        self,
        prompt: str,
        duration: Optional[int] = ToolConfig.DEFAULT_AUDIO_DURATION,
        seed: Optional[int] = None,
        temperature: Optional[float] = ToolConfig.DEFAULT_AUDIO_TEMPERATURE
    ) -> str:
        """
        Generate audio from the given prompt.
        
        Args:
            prompt: Text prompt for audio generation
            duration: Duration in seconds
            seed: Random seed for generation
            temperature: Controls randomness (0.0 to 1.0)
            
        Returns:
            JSON string containing generation results
        """
        try:
            if not self.artifact_handler.session_id:
                logger.error("No session ID set for audio generation")
                return AudioGenerationResponse(
                    status=ToolResponseStatus.ERROR,
                    error="Internal error: No session ID available"
                ).to_string()
            
            logger.info(f"Generating audio for prompt: {prompt}")
            logger.debug(f"Parameters: duration={duration}, seed={seed}, temperature={temperature}")
            
            # Create configuration
            config = AudioGenerationConfig(
                prompt=prompt,
                duration=duration,
                seed=seed,
                temperature=temperature
            )
            
            # Generate audio
            audio_path = self.generator.generate_audio(config)
            
            # Encode audio file
            audio_base64 = self._encode_audio_file(audio_path)
            
            # Store audio as artifact
            self.artifact_handler.add_artifact(audio_base64, ArtifactType.AUDIO.value)
            
            # Return success response
            return AudioGenerationResponse(
                status=ToolResponseStatus.SUCCESS,
                message="Audio generated successfully. Note: The audio is displayed in the UI for the user in the artifacts section.",
                audio_key=str(audio_path)
            ).to_string()
            
        except AudioGenerationError as e:
            error_msg = f"Audio generation failed: {str(e)}"
            logger.error(error_msg)
            return AudioGenerationResponse(
                status=ToolResponseStatus.ERROR,
                error=error_msg
            ).to_string()
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return AudioGenerationResponse(
                status=ToolResponseStatus.ERROR,
                error=error_msg
            ).to_string() 
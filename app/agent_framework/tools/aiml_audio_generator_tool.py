"""AIML Audio Generator Tool
====================

Tool for generating audio using the AIML API's stable-audio model.

Public Components:
- AIMLAudioGeneratorTool: Tool class for generating audio from text prompts
- generate_audio(): Main function for generating audio content

Design Decisions:
- Implements proper error handling and logging
- Supports configurable audio parameters
- Uses pathlib for cross-platform path handling
- Follows project's tool pattern
- Returns base64 encoded audio for direct usage
- Saves generated audio files to logs/audio directory
- Stores generated audio as artifacts for UI display
- Uses session-based artifact storage

Integration Notes:
- Requires AIML_API_KEY environment variable
- Controlled by USE_AUDIO_MOCK_IF_AVAILABLE environment variable
- Saves generated audio to logs/audio directory
- Uses project's logging configuration
- Integrates with UI artifact display system
"""

import json
import os
import sys
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from smolagents import Tool
from app.audio_generators.aiml_api import AudioGenerationConfig, AudioGenerator
from app.models.artifact import Artifact, ArtifactType
from utils.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class AudioGenerationResponse:
    """Response class for audio generation results."""
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

class AIMLAudioGeneratorTool(Tool):
    """Tool for generating audio using AIML API."""
    
    name = "generate_audio"
    description = """
    This tool generates audio content from text prompts using AIML API.
    It returns a JSON string containing the generation results or error message.
    """
    inputs = {
        "prompt": {
            "type": "string",
            "description": "Text prompt describing the desired audio",
        },
        "duration": {
            "type": "integer",
            "description": "Duration in seconds (default: 10)",
            "nullable": True
        },
        "seed": {
            "type": "integer",
            "description": "Random seed for generation",
            "nullable": True
        },
        "temperature": {
            "type": "number",
            "description": "Controls randomness (0.0 to 1.0, default: 0.7)",
            "nullable": True
        }
    }
    output_type = "string"  # Returns JSON string
    
    def __init__(self, session_id: str = None, artifacts: List = None):
        """
        Initialize the audio generator tool.
        
        Args:
            session_id: Optional session ID for tracking artifacts
            artifacts: Optional list for storing generated artifacts
        """
        super().__init__()
        try:
            self.generator = AudioGenerator()
            self.set_session_id(session_id)
            self.artifacts = artifacts
            logger.info("AIMLAudioGeneratorTool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AIMLAudioGeneratorTool: {str(e)}")
            raise
            
    def set_session_id(self, session_id: str) -> None:
        """Set the current session ID for the tool."""
        self.current_session_id = session_id
    
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
        duration: Optional[int] = 10,
        seed: Optional[int] = None,
        temperature: Optional[float] = 0.7
    ) -> str:
        """
        Generate audio from the given prompt.
        
        Args:
            prompt: Text prompt for audio generation
            duration: Duration in seconds (default: 10)
            seed: Random seed for generation (optional)
            temperature: Controls randomness (0.0 to 1.0, default: 0.7)
            
        Returns:
            JSON string containing:
                success: Boolean indicating if generation was successful
                message: Success message if generation succeeded
                error: Optional error message if generation failed
        """
        try:
            if not self.current_session_id:
                logger.error("No session ID set for audio generation")
                return AudioGenerationResponse(
                    success=False,
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
            
            # Encode audio to base64
            base64_audio = self._encode_audio_file(audio_path)
            
            # Store audio as artifact if artifacts list is available
            if self.artifacts is not None:
                self.artifacts.append(Artifact(
                    is_new=True,
                    content=base64_audio,
                    type=ArtifactType.AUDIO
                ))
                
                logger.info("Audio stored as artifact for UI display")
                
            return AudioGenerationResponse(
                success=True,
                message="Audio generated successfully. Note: The audio is displayed in the UI for the user in the artifacts section.",
                error=None
            ).to_string()
            
        except Exception as e:
            error_msg = f"Failed to generate audio: {str(e)}"
            logger.error(error_msg)
            return AudioGenerationResponse(
                success=False,
                error=error_msg
            ).__dict__

def generate_audio(
    prompt: str,
    duration: int = 10,
    seed: Optional[int] = None,
    temperature: float = 0.7
) -> Dict[str, Any]:
    """
    Convenience function to generate audio without directly instantiating the tool.
    
    Args:
        prompt: Text prompt for audio generation
        duration: Duration in seconds (default: 10)
        seed: Random seed for generation (optional)
        temperature: Controls randomness (0.0 to 1.0, default: 0.7)
    
    Returns:
        Dictionary containing generation results
    """
    tool = AIMLAudioGeneratorTool()
    return tool.forward(prompt, duration, seed, temperature)

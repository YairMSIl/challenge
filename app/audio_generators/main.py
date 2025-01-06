"""Suno Audio Generator Demo
=====================

Demonstrates the usage of the SunoAudioGenerator class for generating audio from text prompts.

This script shows:
1. Basic audio generation
2. Error handling
3. Using custom options
4. Mock response handling

Usage:
    python -m app.audio_generators.main

Note:
    Requires SUNO_API_KEY in environment variables
    USE_AUDIO_MOCK_IF_AVAILABLE controls mock usage (defaults to True)
"""

import asyncio
import uuid
from pathlib import Path
from typing import Dict, Any
from .sunobox import suno_audio_generator
from utils.logging_config import get_logger

# Get logger instance
logger = get_logger(__name__)

async def generate_sample_audio(prompt: str, options: Dict[str, Any] = None) -> None:
    """
    Generate a sample audio file from the given prompt.
    
    Args:
        prompt: Text prompt for audio generation
        options: Optional parameters for generation
    """
    try:
        # Generate a unique session ID
        session_id = str(uuid.uuid4())
        
        # Generate audio
        result = await suno_audio_generator.generate_audio(
            prompt=prompt,
            session_id=session_id,
            options=options
        )
        
        if result["error"]:
            logger.error(f"Failed to generate audio: {result['message']}")
            return
            
        # Print the path to the generated audio
        audio_path = Path(result["audio_path"])
        logger.info(f"Audio generated successfully!")
        logger.info(f"Audio file saved at: {audio_path}")
        logger.info(f"File size: {audio_path.stat().st_size / 1024:.2f} KB")
        
    except Exception as e:
        logger.error(f"Error in generate_sample_audio: {str(e)}")

async def main():
    """Main demonstration function."""
    try:
        # Example 1: Basic audio generation
        logger.info("Example 1: Basic audio generation")
        await generate_sample_audio(
            prompt="A cheerful melody with piano and strings"
        )
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main()) 
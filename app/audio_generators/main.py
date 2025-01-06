"""Audio Generation Demo
===================

Demonstrates the usage of the AIML API audio generation functionality.

This script provides examples of:
- Basic audio generation
- Mock response handling
- Different configuration options
- Error handling

Design Decisions:
- Implements mock support for testing
- Provides multiple example configurations
- Demonstrates error handling patterns

Integration Notes:
- Set USE_AUDIO_MOCK_IF_AVAILABLE in .env to control mock usage
- Audio files are saved to logs/audio
- Mock responses are saved to mock/audio
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from dotenv import load_dotenv
from app.audio_generators.aiml_api import generate_audio, AudioGenerationConfig, AudioGenerator
from utils.logging_config import get_logger

# Initialize logging
logger = get_logger(__name__)

def generate_sample_audio():
    """Generate sample audio with different configurations."""
    try:
        # Example: Basic audio generation
        logger.info("Generating peaceful piano melody...")
        audio_file = generate_audio(
            prompt="A peaceful piano melody with soft strings in the background",
            duration=10
        )
        logger.info(f"Piano melody generated: {audio_file}")

    except Exception as e:
        logger.error(f"Error during audio generation: {str(e)}")
        raise

def main():
    """Main entry point for the demo."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Create necessary directories
        Path("logs/audio").mkdir(parents=True, exist_ok=True)
        Path("mock/audio").mkdir(parents=True, exist_ok=True)

        logger.info("Starting audio generation demo...")
        generate_sample_audio()
        logger.info("Demo completed successfully!")

    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")
        return 1

    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code) 
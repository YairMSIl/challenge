"""Image Generation Test Script
=========================

Test script for Eden AI image generation functionality.
Run this script from the app/image_generators directory.
"""

import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from app.image_generators.eden_image import eden_image_generator
from utils.logging_config import get_logger

logger = get_logger(__name__)

def test_image_generation():
    """Test the Eden AI image generation functionality."""
    try:
        # Test prompt
        prompt = "A futuristic cityscape with flying cars and neon lights, digital art style"
        
        logger.info("Starting image generation test...")
        
        # Generate image with custom resolution
        image_path = eden_image_generator.generate_image(
            prompt=prompt,
            session_id="test_session",
            options={"resolution": "256x256"}
        )
        
        logger.info(f"Test completed successfully! Image saved at: {image_path}")
        
    except ValueError as e:
        logger.error(f"Test failed with ValueError: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Test failed with unexpected error: {str(e)}")
        raise

if __name__ == "__main__":
    test_image_generation() 
"""Eden AI Image Utilities
=====================

Utility functions for image handling and processing.

Design Decisions:
- Separates image processing logic from main generator
- Handles file system operations
- Provides base64 encoding/decoding
- Implements safe file naming
"""

import base64
from pathlib import Path
from typing import Optional
from datetime import datetime
from ..exceptions.eden_exceptions import ImageSaveError
from ..config.constants import LOGS_DIR, ImageFormat

def decode_base64_image(image_data: str) -> bytes:
    """
    Decode base64 image data to bytes.
    
    Args:
        image_data: Base64 encoded image string
        
    Returns:
        Decoded image bytes
    """
    try:
        # Handle data URI format
        if ',' in image_data:
            image_data = image_data.split(',', 1)[1]
        return base64.b64decode(image_data)
    except Exception as e:
        raise ImageSaveError("Failed to decode base64 image data", {"error": str(e)})

def create_safe_filename(prompt: str, format: str = ImageFormat.PNG) -> str:
    """
    Create a safe filename from the prompt.
    
    Args:
        prompt: Image generation prompt
        format: Image format extension
        
    Returns:
        Safe filename string
    """
    # Take first 30 chars and make safe
    safe_prompt = "".join(x for x in prompt[:30] if x.isalnum() or x in (' ', '-', '_')).strip()
    safe_prompt = safe_prompt.replace(' ', '_')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"eden_{safe_prompt}_{timestamp}.{format}"

def save_debug_image(image_data: str, prompt: str) -> Optional[str]:
    """
    Save image data to debug directory.
    
    Args:
        image_data: Base64 encoded image data
        prompt: Generation prompt for filename
        
    Returns:
        Path to saved image if successful, None otherwise
    """
    try:
        # Ensure directory exists
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Create filename and save
        filename = create_safe_filename(prompt)
        filepath = LOGS_DIR / filename
        
        image_bytes = decode_base64_image(image_data)
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
            
        return str(filepath)
        
    except Exception as e:
        raise ImageSaveError(f"Failed to save debug image: {str(e)}") 
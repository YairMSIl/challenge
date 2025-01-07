"""Eden AI Configuration Constants
=========================

Constants used throughout the Eden AI image generation module.

Design Decisions:
- All configuration values are centralized here
- Constants are grouped by purpose
- Values can be overridden via environment variables
"""

from enum import Enum
from pathlib import Path

# API Configuration
API_URL = "https://api.edenai.run/v2/image/generation"
DEFAULT_PROVIDER = "openai"
DEFAULT_MODEL = "dall-e-2"
DEFAULT_RESOLUTION = "256x256"
DEFAULT_NUM_IMAGES = 1

# Environment Variables
ENV_API_KEY = "EDEN_API_KEY"
ENV_USE_MOCK = "USE_IMAGE_MOCK_IF_AVAILABLE"

# File System
MOCK_DIR = Path("mock")
LOGS_DIR = Path("logs/images")
MOCK_RESPONSE_PREFIX = "eden_response_"
MOCK_RESPONSE_SUFFIX = ".json"

# Cost Configuration
BASE_COST = 0.016  # Eden AI's DALL-E 2 cost for 256x256 images

class ImageFormat(str, Enum):
    """Supported image formats."""
    PNG = "png"
    JPEG = "jpeg"
    
class ResponseStatus(str, Enum):
    """API response status types."""
    SUCCESS = "success"
    ERROR = "error"

class MockConfig(str, Enum):
    """Mock configuration options."""
    ENABLED = "true"
    DISABLED = "false" 
"""Constants for Audio Generation Service
==================================

Contains all constant values used across the audio generation service.

Design Decisions:
- Groups constants by their purpose
- Uses descriptive names
- Provides type hints where applicable
"""

from pathlib import Path

# API Constants
API_BASE_URL = "https://api.aimlapi.com/v2/generate/audio"
API_MODEL = "stable-audio"
API_CONTENT_TYPE = "application/json"
API_STEPS = 10

# Environment Variables
ENV_API_KEY = "AIML_API_KEY"
ENV_USE_MOCK = "USE_AUDIO_MOCK_IF_AVAILABLE"
ENV_DEFAULT_API_KEY = "394dd5909c0d49c3becfe44e25eeb284"
ENV_DEFAULT_USE_MOCK = "True"

# File System
AUDIO_DIR = Path("logs/audio")
MOCK_DIR = Path("mock/audio")
MOCK_CREATION_DIR = MOCK_DIR / "creation"
MOCK_RETRIEVAL_DIR = MOCK_DIR / "retrieval"

# File Naming
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
AUDIO_FILE_PREFIX = "generated_audio"
MOCK_FILE_PREFIX = "aiml_response"
AUDIO_FILE_EXT = ".wav"
MOCK_FILE_EXT = ".json"

# HTTP Status Codes
HTTP_CREATED = 201
HTTP_OK = 200

# Polling Configuration
POLLING_MAX_ATTEMPTS = 30  # 5 minutes total
POLLING_INTERVAL = 10  # seconds

# Generation Status
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

# Default Generation Parameters
DEFAULT_DURATION = 2
DEFAULT_MODEL_VERSION = "v1"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_K = 250
DEFAULT_TOP_P = 0.99 
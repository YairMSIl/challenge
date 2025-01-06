"""Tool Constants
==============

Constants and configuration values used across tools.

Public Components:
- ArtifactTypes: Enum for artifact types
- ToolNames: Enum for tool names
- ToolConfig: Configuration constants

Design Decisions:
- Uses enums for type safety
- Centralizes configuration values
- Provides descriptive names for magic values
- Separates configuration from implementation
"""

from enum import Enum, auto
from typing import Dict, Any

class ArtifactType(Enum):
    """Enum for artifact types."""
    AUDIO = "audio"
    IMAGE = "image"
    TEXT = "text"
    RESEARCH = "research"
    SEARCH = "search"

class ToolName(Enum):
    """Enum for tool names."""
    AUDIO_GENERATOR = "generate_audio"
    IMAGE_GENERATOR = "generate_image"
    RESEARCH = "research"
    GOOGLE_SEARCH = "google_search"

class ToolConfig:
    """Configuration constants for tools."""
    
    # Audio generation defaults
    DEFAULT_AUDIO_DURATION = 10
    DEFAULT_AUDIO_TEMPERATURE = 0.7
    
    # Image generation defaults
    DEFAULT_IMAGE_RESOLUTION = "256x256"
    
    # Google search limits
    MAX_SEARCH_RESULTS = 10
    MIN_SEARCH_RESULTS = 1
    DEFAULT_SEARCH_RESULTS = 5
    
    # Mock configuration keys
    USE_AUDIO_MOCK_KEY = "USE_AUDIO_MOCK_IF_AVAILABLE"
    USE_SEARCH_MOCK_KEY = "USE_SEARCH_MOCK_IF_AVAILABLE"
    USE_IMAGE_MOCK_KEY = "USE_IMAGE_MOCK_IF_AVAILABLE"
    
    # Environment variable keys
    GOOGLE_API_KEY = "GOOGLE_API_KEY"
    GOOGLE_CSE_ID = "GOOGLE_CSE_ID"
    AIML_API_KEY = "AIML_API_KEY"
    EDEN_API_KEY = "EDEN_API_KEY"
    
    # Directory paths
    MOCK_DIR = "mock"
    AUDIO_DIR = "audio"
    IMAGE_DIR = "images"

# Tool input schemas
AUDIO_TOOL_INPUTS = {
    "prompt": {
        "type": "string",
        "description": "Text prompt describing the desired audio",
    },
    "duration": {
        "type": "integer",
        "description": f"Duration in seconds (default: {ToolConfig.DEFAULT_AUDIO_DURATION})",
        "nullable": True
    },
    "seed": {
        "type": "integer",
        "description": "Random seed for generation",
        "nullable": True
    },
    "temperature": {
        "type": "number",
        "description": f"Controls randomness (0.0 to 1.0, default: {ToolConfig.DEFAULT_AUDIO_TEMPERATURE})",
        "nullable": True
    }
}

IMAGE_TOOL_INPUTS = {
    "prompt": {
        "type": "string",
        "description": "Text description of the image to generate",
    }
}

SEARCH_TOOL_INPUTS = {
    "query": {
        "type": "string",
        "description": "The search query to execute",
    },
    "num_results": {
        "type": "integer",
        "description": f"Number of results to return (max {ToolConfig.MAX_SEARCH_RESULTS}, default {ToolConfig.DEFAULT_SEARCH_RESULTS})",
        "nullable": True
    }
}

RESEARCH_TOOL_INPUTS = {
    "query": {
        "type": "string",
        "description": "Research topic or question to investigate",
    }
} 
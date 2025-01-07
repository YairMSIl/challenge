"""Configuration Models for Audio Generation
====================================

Contains all configuration related models used in the audio generation service.

Design Decisions:
- Uses dataclasses for clean configuration management
- Implements proper validation
- Provides sensible defaults
- Uses type hints for better IDE support
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from ..constants import (
    DEFAULT_DURATION, DEFAULT_MODEL_VERSION,
    DEFAULT_TEMPERATURE, DEFAULT_TOP_K, DEFAULT_TOP_P
)

@dataclass
class AudioGenerationConfig:
    """Configuration for audio generation."""
    prompt: str
    duration: int = DEFAULT_DURATION
    seed: Optional[int] = None
    model_version: str = DEFAULT_MODEL_VERSION
    temperature: float = DEFAULT_TEMPERATURE
    top_k: int = DEFAULT_TOP_K
    top_p: float = DEFAULT_TOP_P

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.prompt:
            raise ValueError("Prompt cannot be empty")
        if self.duration < 1:
            raise ValueError("Duration must be at least 1 second")
        if self.temperature < 0 or self.temperature > 1:
            raise ValueError("Temperature must be between 0 and 1")
        if self.top_k < 1:
            raise ValueError("top_k must be greater than 0")
        if self.top_p <= 0 or self.top_p > 1:
            raise ValueError("top_p must be between 0 and 1")

    def to_api_payload(self) -> Dict[str, Any]:
        """Convert config to API payload."""
        payload = {
            "model": "stable-audio",
            "prompt": self.prompt,
            "steps": 10,
            "seconds_total": self.duration
        }
        
        if self.seed is not None:
            payload["seed"] = self.seed
            
        return payload

@dataclass
class MockConfig:
    """Configuration for mock behavior."""
    enabled: bool = True
    mock_dir: str = field(default="mock/audio")
    save_responses: bool = True 
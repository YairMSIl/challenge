"""Audio Generation Package
=====================

Main package for audio generation using AIML API.

Public Components:
- AudioGenerator: Main class for generating audio
- AudioGenerationConfig: Configuration for audio generation
- AudioGenerationError: Base exception class
- generate_audio(): Convenience function for simple generation

Design Decisions:
- Exposes minimal public interface
- Hides implementation details
- Provides convenience functions
- Uses proper error handling
"""

from .services.generator import AudioGenerator
from .models.config import AudioGenerationConfig
from .models.exceptions import AudioGenerationError
from pathlib import Path
from typing import Optional

def generate_audio(
    prompt: str,
    duration: int = 10,
    seed: Optional[int] = None,
    temperature: float = 0.7
) -> Path:
    """
    Convenience function to generate audio without directly instantiating AudioGenerator.
    
    Args:
        prompt: Text prompt for audio generation
        duration: Duration in seconds (default: 10)
        seed: Random seed for generation (optional)
        temperature: Controls randomness (0.0 to 1.0, default: 0.7)
    
    Returns:
        Path to the generated audio file
    """
    config = AudioGenerationConfig(
        prompt=prompt,
        duration=duration,
        seed=seed,
        temperature=temperature
    )
    
    generator = AudioGenerator()
    return generator.generate_audio(config)

__all__ = [
    'AudioGenerator',
    'AudioGenerationConfig',
    'AudioGenerationError',
    'generate_audio'
] 
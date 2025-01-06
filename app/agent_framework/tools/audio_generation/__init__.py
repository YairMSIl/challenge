"""Audio Generation Tool Package
=========================

Tool for generating audio using AIML API.

Public Components:
- AudioGenerationTool: Main tool class for generating audio
- AudioGenerationResponse: Response class for generation results

Design Decisions:
- Splits functionality into focused modules
- Uses proper dependency injection
- Implements clean separation of concerns
"""

from .tool import AudioGenerationTool
from .audio_response import AudioGenerationResponse

__all__ = ['AudioGenerationTool', 'AudioGenerationResponse'] 
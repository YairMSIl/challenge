"""Audio Generators Package
=====================

Contains implementations of various audio generation services.

Public Components:
- SunoAudioGenerator: Audio generation using Suno's API
"""

from .sunobox import suno_audio_generator

__all__ = ['suno_audio_generator'] 
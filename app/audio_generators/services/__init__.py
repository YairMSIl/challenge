"""Services Package for Audio Generation
================================

Contains all service classes used in the audio generation service.

Public Components:
- AudioGenerator: Main generation service
- MockService: Mock response handling
- StorageService: File storage operations

Design Decisions:
- Separates concerns into focused services
- Uses dependency injection
- Implements proper error handling
"""

from .generator import AudioGenerator
from .mock_service import MockService
from .storage_service import StorageService

__all__ = [
    'AudioGenerator',
    'MockService',
    'StorageService'
] 
"""Audio Generation Service
=====================

Main service for generating audio using AIML API.

Design Decisions:
- Separates concerns into focused services
- Uses dependency injection for better testing
- Implements proper error handling
- Follows single responsibility principle
"""

import os
import requests
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from ..models.config import AudioGenerationConfig, MockConfig
from ..models.response import GenerationResponse
from ..models.exceptions import (
    APIError, NetworkError, ValidationError
)
from ..enums import MockType
from ..constants import (
    ENV_API_KEY, ENV_USE_MOCK, ENV_DEFAULT_API_KEY,
    ENV_DEFAULT_USE_MOCK, API_BASE_URL, API_CONTENT_TYPE,
    HTTP_CREATED, HTTP_OK
)
from .mock_service import MockService
from .storage_service import StorageService
from utils.logging_config import get_logger

logger = get_logger(__name__)

class AudioGenerator:
    """Main service for audio generation."""
    
    def __init__(self):
        """Initialize the audio generator with required services."""
        load_dotenv()
        
        self.api_key = os.getenv(ENV_API_KEY, ENV_DEFAULT_API_KEY)
        if not self.api_key:
            raise ValidationError("API key is required", "api_key")
            
        use_mock = os.getenv(ENV_USE_MOCK, ENV_DEFAULT_USE_MOCK).lower()
        mock_config = MockConfig(enabled=(use_mock == 'true'))
        
        self.mock_service = MockService(mock_config)
        self.storage_service = StorageService()
        
    def _get_headers(self) -> dict:
        """Get API request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": API_CONTENT_TYPE
        }
        
    def create_generation_job(
        self,
        config: AudioGenerationConfig
    ) -> GenerationResponse:
        """
        Create a new audio generation job.
        
        Args:
            config: Configuration for audio generation
            
        Returns:
            GenerationResponse object
        """
        try:
            # Check for mock response
            mock_response = self.mock_service.get_response(MockType.CREATION)
            if mock_response is not None:
                return GenerationResponse.from_dict(mock_response)
                
            # Make API request
            response = requests.post(
                API_BASE_URL,
                headers=self._get_headers(),
                json=config.to_api_payload()
            )
            
            response_data = response.json()
            self.mock_service.save_response(response_data, MockType.CREATION)
            
            if response.status_code != HTTP_CREATED:
                raise APIError(
                    "Failed to create generation job",
                    response.status_code,
                    response_data
                )
                
            return GenerationResponse.from_dict(response_data)
            
        except requests.exceptions.RequestException as e:
            raise NetworkError("Network error during job creation", e)
            
    def poll_generation_job(
        self,
        generation_id: str
    ) -> GenerationResponse:
        """
        Poll an existing generation job until completion.
        
        Args:
            generation_id: ID of the generation job
            
        Returns:
            GenerationResponse object
        """
        try:
            # Check for mock response
            mock_response = self.mock_service.get_response(MockType.RETRIEVAL)
            if mock_response is not None:
                return GenerationResponse.from_dict(mock_response)
                
            # Make API request
            response = requests.get(
                API_BASE_URL,
                params={"generation_id": generation_id},
                headers=self._get_headers()
            )
            
            response_data = response.json()
            self.mock_service.save_response(response_data, MockType.RETRIEVAL)
            
            if response.status_code != HTTP_OK:
                raise APIError(
                    "Failed to check generation status",
                    response.status_code,
                    response_data
                )
                
            return GenerationResponse.from_dict(response_data)
            
        except requests.exceptions.RequestException as e:
            raise NetworkError("Network error during status check", e)
            
    def download_audio(self, url: str) -> bytes:
        """
        Download audio file from URL.
        
        Args:
            url: URL of the audio file
            
        Returns:
            Raw audio data
        """
        try:
            response = requests.get(url)
            if response.status_code != HTTP_OK:
                raise APIError(
                    "Failed to download audio file",
                    response.status_code
                )
            return response.content
            
        except requests.exceptions.RequestException as e:
            raise NetworkError("Network error during audio download", e)
            
    def generate_audio(self, config: AudioGenerationConfig) -> Path:
        """
        Generate audio from the given configuration.
        
        Args:
            config: Configuration for audio generation
            
        Returns:
            Path to the generated audio file
        """
        try:
            # Create generation job
            job_response = self.create_generation_job(config)
            
            # Poll for completion
            while not (job_response.is_complete() or job_response.is_failed()):
                job_response = self.poll_generation_job(job_response.id)
                
            if job_response.is_failed():
                raise APIError(
                    "Generation failed",
                    response_data={"error": job_response.error}
                )
                
            if not job_response.audio_file:
                raise APIError("No audio file in completed response")
                
            # Download and save audio
            audio_data = self.download_audio(job_response.audio_file.url)
            return self.storage_service.save_audio(audio_data)
            
        except Exception as e:
            logger.error(f"Audio generation failed: {str(e)}")
            raise 
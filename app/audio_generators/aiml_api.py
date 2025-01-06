"""Audio Generation Service
====================

Handles audio generation using the AIML API's stable-audio model.

Public Components:
- generate_audio(): Main function for generating audio from text prompts
- AudioGenerationConfig: Configuration dataclass for audio generation
- create_generation_job(): Creates a new audio generation job
- poll_generation_job(): Polls an existing job until completion

Design Decisions:
- Uses requests library for HTTP requests
- Saves raw API responses for debugging and mocking
- Implements robust error handling and logging
- Supports configurable audio parameters
- Uses pathlib for cross-platform path handling
- Supports mock responses for testing (controlled via USE_AUDIO_MOCK_IF_AVAILABLE)
- Separates mocks by type (creation vs retrieval) for accurate testing
- Separates job creation and polling for better testing and mock handling

Integration Notes:
- Requires AIML_API_KEY environment variable
- USE_AUDIO_MOCK_IF_AVAILABLE controls mock usage (defaults to True)
- Saves generated audio to logs/audio directory
- Saves API responses to mock/audio/[type] directory
- Uses project's logging configuration
"""

import os
import json
import time
import requests
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from utils.logging_config import get_logger

logger = get_logger(__name__)

def str_to_bool(value: str) -> bool:
    """Convert string to boolean."""
    return value.lower() in ('true', 't', 'yes', 'y', '1', 'on')

@dataclass
class AudioGenerationConfig:
    """Configuration for audio generation."""
    prompt: str
    duration: int = 2  # Duration in seconds
    seed: Optional[int] = None
    model_version: str = "v1"
    temperature: float = 0.7
    top_k: int = 250
    top_p: float = 0.99

class AIMLAPIException(Exception):
    """Custom exception for AIML API errors."""
    pass

class AudioGenerator:
    """Handles audio generation using AIML API."""
    
    BASE_URL = "https://api.aimlapi.com/v2/generate/audio"
    
    def __init__(self):
        """Initialize the audio generator with configuration."""
        load_dotenv()
        
        # Get API key from environment
        self.api_key = os.getenv("AIML_API_KEY", "394dd5909c0d49c3becfe44e25eeb284")
        if not self.api_key:
            logger.error("AIML_API_KEY not found in environment variables")
            raise ValueError("AIML_API_KEY is required")
            
        # Get mock configuration
        self.use_mock = str_to_bool(os.getenv('USE_AUDIO_MOCK_IF_AVAILABLE', 'True'))
        logger.debug(f"Mock usage configuration: {self.use_mock}")
        
        self.setup_directories()
    
    def setup_directories(self):
        """Create necessary directories if they don't exist."""
        self.audio_dir = Path("logs/audio")
        self.mock_dir = Path("mock/audio")
        self.mock_creation_dir = self.mock_dir / "creation"
        self.mock_retrieval_dir = self.mock_dir / "retrieval"
        
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.mock_dir.mkdir(parents=True, exist_ok=True)
        self.mock_creation_dir.mkdir(parents=True, exist_ok=True)
        self.mock_retrieval_dir.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"Directories initialized: audio_dir={self.audio_dir}, mock_dir={self.mock_dir}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for file naming."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _save_api_response(self, response_data: Dict[str, Any], timestamp: str, mock_type: str = "creation"):
        """
        Save API response to mock directory.
        
        Args:
            response_data: The API response data to save
            timestamp: Timestamp for the filename
            mock_type: Type of mock ('creation' or 'retrieval')
        """
        mock_subdir = self.mock_creation_dir if mock_type == "creation" else self.mock_retrieval_dir
        mock_file = mock_subdir / f"aiml_response_{timestamp}.json"
        logger.debug(f"Saving {mock_type} API response to {mock_file}")
        
        try:
            with open(mock_file, 'w') as f:
                json.dump(response_data, f, indent=2)
            logger.debug(f"Successfully saved {mock_type} API response to {mock_file}")
        except Exception as e:
            logger.error(f"Failed to save {mock_type} API response: {str(e)}")
    
    def _get_mock_response(self, mock_type: str = "creation") -> Optional[Dict[str, Any]]:
        """
        Get the most recent mock response if available.
        
        Args:
            mock_type: Type of mock to retrieve ('creation' or 'retrieval')
            
        Returns:
            Mock response data if available, None otherwise
        """
        try:
            mock_subdir = self.mock_creation_dir if mock_type == "creation" else self.mock_retrieval_dir
            if not mock_subdir.exists():
                return None
                
            # Get all aiml response files for the specific type
            mock_files = list(mock_subdir.glob("aiml_response_*.json"))
            if not mock_files:
                return None
                
            # Get most recent file
            latest_mock = max(mock_files, key=lambda p: p.stat().st_mtime)
            logger.debug(f"Found {mock_type} mock response file: {latest_mock}")
            
            with open(latest_mock, 'r', encoding='utf-8') as f:
                mock_data = json.load(f)
                
            logger.info(f"Using {mock_type} mock response instead of making API call")
            return mock_data
            
        except Exception as e:
            logger.error(f"Failed to load {mock_type} mock response: {str(e)}")
            return None

    def create_generation_job(self, config: AudioGenerationConfig) -> Dict[str, Any]:
        """
        Create a new audio generation job.
        
        Args:
            config: AudioGenerationConfig instance with generation parameters
            
        Returns:
            Dict containing the job information including generation_id
            
        Raises:
            AIMLAPIException: If job creation fails
        """
        timestamp = self._get_timestamp()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "stable-audio",  # Required by the API
            "prompt": config.prompt,
            "steps": 10,
            "seconds_total": config.duration
        }
        
        if config.seed is not None:
            payload["seed"] = config.seed
        
        logger.info(f"Creating audio generation job with prompt: {config.prompt}")
        logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
        logger.debug(f"API URL: {self.BASE_URL}")
        
        try:
            # Check for mock response if enabled
            response_data = self._get_mock_response("creation") if self.use_mock else None
            
            if response_data is None:
                if self.use_mock:
                    logger.debug("No creation mock response available, falling back to API call")
                else:
                    logger.debug("Mock disabled, making API call")
                
                response = requests.post(
                    self.BASE_URL,
                    headers=headers,
                    json=payload
                )
                response_text = response.text
                logger.debug(f"Raw API response: {response_text}")
                
                try:
                    response_data = json.loads(response_text)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse API response as JSON: {str(e)}")
                    logger.error(f"Response text: {response_text}")
                    raise AIMLAPIException(f"Invalid JSON response from API: {str(e)}")
                
                # Save raw API response for future mocking
                self._save_api_response(response_data, timestamp, "creation")
                
                if response.status_code != 201:  # API returns 201 for successful creation
                    error_msg = response_data.get('error', {}).get('message', 'Unknown error')
                    logger.error(f"API request failed with status {response.status_code}: {error_msg}")
                    logger.error(f"Full response: {json.dumps(response_data, indent=2)}")
                    raise AIMLAPIException(f"API request failed: {error_msg}")
            
            # Validate response data
            generation_id = response_data.get('id')
            if not generation_id:
                logger.error("No generation_id in response")
                logger.error(f"Response data: {json.dumps(response_data, indent=2)}")
                raise AIMLAPIException("Missing generation_id in API response")
                
            logger.info(f"Audio generation job created with ID: {generation_id}")
            return response_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during job creation: {str(e)}")
            raise AIMLAPIException(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during job creation: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {str(e)}")
            raise

    def poll_generation_job(self, generation_id: str) -> Dict[str, Any]:
        """
        Poll an existing generation job until completion.
        
        Args:
            generation_id: The ID of the generation job to poll
            
        Returns:
            Dict containing the completed generation data including audio_url
            
        Raises:
            AIMLAPIException: If polling fails or times out
        """
        timestamp = self._get_timestamp()
        params = {"generation_id": generation_id}
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Check for mock response first
        mock_response = self._get_mock_response("retrieval") if self.use_mock else None
        if mock_response is not None:
            return mock_response
            
        max_attempts = 30  # 5 minutes total (10 second intervals)
        attempt = 0
        
        while attempt < max_attempts:
            try:
                response = requests.get(
                    self.BASE_URL,
                    params=params,
                    headers=headers
                )
                response_data = response.json()
                
                # Save response for future mocking
                self._save_api_response(response_data, timestamp, "retrieval")
                
                if response.status_code != 200:
                    logger.error(f"Raw response data: {response_data}")
                    error_msg = response_data.get('error', {}).get('message', 'Unknown error')
                    logger.error(f"Status check failed: {error_msg}")
                    raise AIMLAPIException(f"Status check failed: {error_msg}")
                
                status = response_data.get('status', '').lower()
                if status == 'completed':
                    logger.info("Generation completed successfully")
                    return response_data
                elif status == 'failed':
                    error_msg = response_data.get('error', {}).get('message', 'Generation failed')
                    logger.error(f"Generation failed: {error_msg}")
                    raise AIMLAPIException(f"Generation failed: {error_msg}")
                
                logger.debug(f"Generation in progress (attempt {attempt + 1}/{max_attempts})")
                logger.debug(f"Current status: {status}")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error during status check: {str(e)}")
                raise AIMLAPIException(f"Network error during status check: {str(e)}")
            
            attempt += 1
            time.sleep(10)  # Wait 10 seconds between checks
        
        raise AIMLAPIException("Generation timed out")

    def _save_audio(self, audio_data: bytes, timestamp: str) -> Path:
        """Save audio data to file."""
        audio_file = self.audio_dir / f"generated_audio_{timestamp}.wav"
        logger.debug(f"Saving audio to {audio_file}")
        
        try:
            with open(audio_file, 'wb') as f:
                f.write(audio_data)
            logger.debug(f"Successfully saved audio to {audio_file}")
            return audio_file
        except Exception as e:
            logger.error(f"Failed to save audio file: {str(e)}")
            raise

    def generate_audio(self, config: AudioGenerationConfig) -> Path:
        """
        Generate audio from the given configuration.
        
        Args:
            config: AudioGenerationConfig instance with generation parameters
            
        Returns:
            Path to the generated audio file
            
        Raises:
            AIMLAPIException: If API request fails
        """
        try:
            # Step 1: Create generation job
            job_data = self.create_generation_job(config)
            generation_id = job_data['id']
            
            # Step 2: Poll for completion
            final_response = self.poll_generation_job(generation_id)
            
            # Step 3: Get audio URL and download
            audio_url = None
            if 'audio_file' in final_response:
                audio_url = final_response['audio_file'].get('url')
            
            if not audio_url:
                logger.error(f"Could not find audio URL in response: {json.dumps(final_response, indent=2)}")
                raise AIMLAPIException("No audio URL found in completed response")
            
            # Step 4: Download audio file
            timestamp = self._get_timestamp()
            response = requests.get(audio_url)
            if response.status_code != 200:
                raise AIMLAPIException(f"Failed to download audio: {response.status_code}")
            audio_data = response.content
            
            # Step 5: Save audio file
            audio_file = self._save_audio(audio_data, timestamp)
            logger.info(f"Successfully generated audio: {audio_file}")
            
            return audio_file
                    
        except Exception as e:
            logger.error(f"Unexpected error during audio generation: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {str(e)}")
            raise

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

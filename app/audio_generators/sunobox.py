"""Suno Audio Generation
=====================

Provides integration with Suno's audio generation service.

Public Components:
- SunoAudioGenerator: Main class for generating audio using Suno
- generate_audio(): Primary method for audio generation
- configure(): Setup function for API configuration

Design Decisions:
- Implements proper error handling and logging
- Integrates with CostTracker for budget management
- Saves audio files to logs/audio directory
- Supports mock responses for testing and cost saving (controlled via USE_AUDIO_MOCK_IF_AVAILABLE)
- Uses async/await for non-blocking audio generation
- Implements retry mechanism for long-running tasks

Integration Notes:
- Requires SUNO_API_KEY in environment variables
- USE_AUDIO_MOCK_IF_AVAILABLE controls mock usage (defaults to True)
- Configurable via logging config
- Uses CostTracker for budget management
"""

import os
import json
import aiohttp
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from utils.logging_config import get_logger
from app.cost_tracker.cost_tracker import CostTracker
import time
import asyncio

# Get logger instance
logger = get_logger(__name__)

def str_to_bool(value: str) -> bool:
    """Convert string to boolean."""
    return value.lower() in ('true', 't', 'yes', 'y', '1', 'on')

class SunoAudioGenerator:
    def __init__(self):
        """Initialize Suno Audio Generator."""
        load_dotenv()
        
        # Get API key from environment
        self.api_key = os.getenv('SUNO_API_KEY')
        if not self.api_key:
            logger.error("SUNO_API_KEY not found in environment variables")
            raise ValueError("SUNO_API_KEY is required")
            
        # Get mock configuration
        self.use_mock = str_to_bool(os.getenv('USE_AUDIO_MOCK_IF_AVAILABLE', 'True'))
        logger.debug(f"Mock usage configuration: {self.use_mock}")
        
        self.api_url = "https://apibox.erweima.ai/api/v1/generate"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Log API configuration (masking the API key)
        masked_headers = self.headers.copy()
        masked_headers["Authorization"] = "Bearer ***" + self.api_key[-4:]
        logger.debug(f"API URL: {self.api_url}")
        logger.debug(f"Headers: {json.dumps(masked_headers, indent=2)}")
        
        self.cost_tracker = CostTracker("suno_audio", self._calculate_request_cost)
        self._ensure_directories()
        logger.info(f"SunoAudioGenerator initialized successfully (mock enabled: {self.use_mock})")

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        # Ensure audio directory
        audio_dir = Path("logs/audio")
        audio_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured audio directory exists at {audio_dir}")
        
        # Ensure mock directory
        mock_dir = Path("mock")
        mock_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured mock directory exists at {mock_dir}")

    def _calculate_request_cost(self, request_data: Dict[str, Any]) -> float:
        """
        Calculate cost for a Suno audio generation request.
        
        Args:
            request_data: Dictionary containing audio generation details
                        May include 'cost' from API response
            
        Returns:
            Calculated cost in dollars
        """
        # If cost is provided in the request data (from API response), use it
        if 'cost' in request_data:
            cost = float(request_data['cost'])
            logger.debug(f"Using cost from API response: ${cost:.6f}")
            return cost
            
        # Otherwise use base cost
        base_cost = 0.01  # Example base cost - adjust based on actual Suno pricing
        logger.debug(f"Using base cost: ${base_cost:.6f}")
        return base_cost

    def _save_mock_response(self, response_content: Any) -> None:
        """Save API response for mock testing."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = Path("mock") / f"suno_response_{timestamp}.json"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(response_content, f, indent=2)
                
            logger.debug(f"Saved mock response to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save mock response: {str(e)}")

    def _get_mock_response(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent mock response if available.
        
        Returns:
            Mock response data if available, None otherwise
        """
        try:
            mock_dir = Path("mock")
            if not mock_dir.exists():
                return None
                
            # Get all suno response files
            mock_files = list(mock_dir.glob("suno_response_*.json"))
            if not mock_files:
                return None
                
            # Get most recent file
            latest_mock = max(mock_files, key=lambda p: p.stat().st_mtime)
            logger.debug(f"Found mock response file: {latest_mock}")
            
            with open(latest_mock, 'r', encoding='utf-8') as f:
                mock_data = json.load(f)
                
            logger.info("Using mock response instead of making API call")
            return mock_data
            
        except Exception as e:
            logger.error(f"Failed to load mock response: {str(e)}")
            return None

    async def _poll_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Poll the task status until completion or failure.
        
        Args:
            task_id: The task ID to poll
            
        Returns:
            The completed task response
            
        Raises:
            Exception: If polling times out or task fails
        """
        status_url = f"{self.api_url}/tasks/{task_id}"
        max_attempts = 60  # 5 minutes with 5-second intervals
        attempt = 0
        
        logger.debug(f"Starting to poll task status. URL: {status_url}")
        logger.debug(f"Task ID: {task_id}")
        logger.debug(f"Max attempts: {max_attempts}")
        
        while attempt < max_attempts:
            try:
                logger.debug(f"Polling attempt {attempt + 1}/{max_attempts}")
                async with aiohttp.ClientSession() as session:
                    async with session.get(status_url, headers=self.headers) as response:
                        try:
                            # Log complete response for debugging
                            response_text = await response.text()
                            response_status = response.status
                            response_headers = dict(response.headers)
                            
                            logger.debug(f"Poll Response Status: {response_status}")
                            logger.debug(f"Poll Response Headers: {json.dumps(response_headers, indent=2)}")
                            logger.debug(f"Poll Response Body length: {len(response_text)} characters")
                            logger.debug(f"Poll Response Body (raw): '{response_text}'")  # Added quotes to see whitespace
                            logger.debug(f"Poll Response Body bytes: {response_text.encode()}")  # See raw bytes
                            
                            # Try to detect content type
                            content_type = response.headers.get('Content-Type', 'unknown')
                            logger.debug(f"Poll Response Content-Type: {content_type}")
                            
                            if not response_text:
                                logger.warning("Received empty poll response body")
                            
                            if response.status != 200:
                                error_msg = f"Status check failed: Status {response_status}"
                                if response_text:
                                    error_msg += f", Body: {response_text}"
                                else:
                                    error_msg += " (Empty response body)"
                                raise Exception(error_msg)
                                
                            try:
                                result = await response.json()
                            except json.JSONDecodeError as e:
                                logger.error(f"Failed to parse JSON response: {str(e)}")
                                logger.error(f"Raw response: {response_text}")
                                raise Exception(f"Invalid JSON response from API: {str(e)}")
                                
                            logger.debug(f"Parsed JSON response: {json.dumps(result, indent=2)}")
                            status = result.get('status')
                            logger.debug(f"Task status: {status}")
                            
                            if status == 'completed':
                                logger.info(f"Task completed successfully after {attempt + 1} attempts")
                                return result
                            elif status == 'failed':
                                error_info = result.get('error', 'Unknown error')
                                logger.error(f"Task failed with error: {error_info}")
                                raise Exception(f"Task failed: {error_info}")
                            
                            # Still processing, wait and try again
                            logger.debug(f"Task still processing, waiting 5 seconds before next attempt")
                            await asyncio.sleep(5)
                            attempt += 1
                            
                        except Exception as e:
                            logger.error(f"Error processing poll response: {str(e)}")
                            logger.error(f"Response status: {response.status}")
                            logger.error(f"Response headers: {dict(response.headers)}")
                            raise
                        
            except Exception as e:
                logger.error(f"Error polling task status: {str(e)}")
                raise
                
        logger.error(f"Task polling timed out after {max_attempts} attempts")
        raise Exception("Task polling timed out")

    def _save_audio(self, audio_data: bytes, prompt: str) -> str:
        """
        Save the audio data to a file.
        
        Args:
            audio_data: Raw audio data
            prompt: The prompt used to generate the audio
            
        Returns:
            Path to the saved audio file
        """
        try:
            safe_prompt = "".join(x for x in prompt[:30] if x.isalnum() or x in (' ', '-', '_')).strip()
            safe_prompt = safe_prompt.replace(' ', '_')
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"suno_{safe_prompt}_{timestamp}.wav"
            filepath = Path("logs/audio") / filename
            
            with open(filepath, 'wb') as f:
                f.write(audio_data)
                
            logger.info(f"Audio saved successfully at {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save audio: {str(e)}")
            raise

    async def generate_audio(
        self,
        prompt: str,
        session_id: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate audio using Suno.
        
        Args:
            prompt: The text prompt for audio generation
            session_id: Unique identifier for the session
            options: Optional configuration parameters
            
        Returns:
            Dictionary containing:
                - audio_path: Path to the generated audio file
                - error: Optional error information if generation failed
            
        Raises:
            ValueError: If the prompt is invalid
            Exception: For other API or system errors
        """
        try:
            logger.debug(f"Generating audio for prompt: {prompt[:50]}...")
            
            # Calculate request cost before making API call
            request_data = {"prompt_length": len(prompt)}
            
            # Check for mock response if enabled
            response_content = self._get_mock_response() if self.use_mock else None
            
            if response_content is None:
                if self.use_mock:
                    logger.debug("No mock response available, falling back to API call")
                else:
                    logger.debug("Mock disabled, making API call")
                    
                # Ensure options is a dict
                options = options or {}
                    
                # No mock available or mock disabled, make actual API call
                payload = {
                    "prompt": prompt,
                    "customMode": False,  # TODO: Make this configurable
                    "instrumental": False,  # TODO: Make this configurable
                    **options
                }
                
                logger.debug(f"Sending request with payload: {json.dumps(payload, indent=2)}")
                
                # Make API request to start generation
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.api_url, json=payload, headers=self.headers) as response:
                        # Log the complete response for debugging
                        try:
                            response_text = await response.text()
                            response_status = response.status
                            response_headers = dict(response.headers)
                            
                            logger.debug(f"API Response Status: {response_status}")
                            logger.debug(f"API Response Headers: {json.dumps(response_headers, indent=2)}")
                            logger.debug(f"API Response Body length: {len(response_text)} characters")
                            logger.debug(f"API Response Body (raw): '{response_text}'")  # Added quotes to see whitespace
                            logger.debug(f"API Response Body bytes: {response_text.encode()}")  # See raw bytes
                            
                            # Try to detect content type
                            content_type = response.headers.get('Content-Type', 'unknown')
                            logger.debug(f"Response Content-Type: {content_type}")
                            
                            if not response_text:
                                logger.warning("Received empty response body")
                            
                            if response.status != 202:  # Assuming 202 Accepted for async tasks
                                error_msg = f"API request failed: Status {response_status}"
                                if response_text:
                                    error_msg += f", Body: {response_text}"
                                else:
                                    error_msg += " (Empty response body)"
                                raise Exception(error_msg)
                                
                            try:
                                init_response = await response.json()
                            except json.JSONDecodeError as e:
                                logger.error(f"Failed to parse JSON response: {str(e)}")
                                logger.error(f"Raw response: {response_text}")
                                raise Exception(f"Invalid JSON response from API: {str(e)}")
                                
                            logger.debug(f"Parsed JSON response: {json.dumps(init_response, indent=2)}")
                            
                            task_id = init_response.get('task_id')
                            
                            if not task_id:
                                raise ValueError(f"No task_id in response. Full response: {json.dumps(init_response, indent=2)}")
                                
                        except Exception as e:
                            logger.error(f"Error processing response: {str(e)}")
                            logger.error(f"Response status: {response.status}")
                            logger.error(f"Response headers: {dict(response.headers)}")
                            raise
                            
                        # Poll for task completion
                        response_content = await self._poll_task_status(task_id)
                        
                        # Only save successful responses to mock
                        self._save_mock_response(response_content)

            # Process response
            if 'error' in response_content:
                error_msg = response_content['error'].get('message', 'Unknown API error')
                logger.error(f"API Error: {error_msg}")
                return {
                    "error": True,
                    "message": error_msg
                }
            
            # Get audio data from response
            try:
                audio_url = response_content.get('audio_url')
                if not audio_url:
                    raise ValueError("No audio URL in response")
                    
                # Download audio file
                async with aiohttp.ClientSession() as session:
                    async with session.get(audio_url) as response:
                        if response.status != 200:
                            raise Exception(f"Failed to download audio: {response.status}")
                        audio_data = await response.read()
                        
                # Save audio file
                audio_path = self._save_audio(audio_data, prompt)
                
            except Exception as e:
                logger.error(f"Failed to process audio data: {str(e)}")
                return {
                    "error": True,
                    "message": f"Failed to process audio data: {str(e)}"
                }
            
            # Track cost
            if 'cost' in response_content:
                request_data['cost'] = response_content['cost']
            self.cost_tracker.calculate_cost(request_data, session_id)
            
            logger.info("Audio generated successfully")
            return {
                "error": False,
                "audio_path": audio_path
            }
            
        except aiohttp.ClientError as e:
            error_msg = f"API request failed: {str(e)}"
            logger.error(error_msg)
            return {
                "error": True,
                "message": error_msg
            }
        except ValueError as e:
            error_msg = f"Invalid request: {str(e)}"
            logger.error(error_msg)
            return {
                "error": True,
                "message": error_msg
            }
        except Exception as e:
            error_msg = f"Audio generation failed: {str(e)}"
            logger.error(error_msg)
            logger.debug(f"Exception type: {type(e)}")
            logger.debug(f"Exception details: {str(e)}")
            return {
                "error": True,
                "message": error_msg
            }

# Singleton instance
suno_audio_generator = SunoAudioGenerator()

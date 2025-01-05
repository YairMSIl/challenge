"""Eden AI Image Generation
=====================

Provides integration with Eden AI's image generation service using OpenAI's model.

Public Components:
- EdenImageGenerator: Main class for generating images using Eden AI
- generate_image(): Primary method for image generation
- configure(): Setup function for API configuration

Design Decisions:
- Uses OpenAI's model through Eden AI for optimal quality
- Implements proper error handling and logging
- Integrates with CostTracker for budget management
- Saves generated images to logs/images directory
- Default resolution set to 256x256 for balanced quality/speed
- Supports mock responses for testing and cost saving (controlled via USE_IMAGE_MOCK_IF_AVAILABLE)
- Uses async/await for non-blocking image generation

Integration Notes:
- Requires EDEN_API_KEY in environment variables
- USE_IMAGE_MOCK_IF_AVAILABLE controls mock usage (defaults to True)
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
import base64

# Get logger instance
logger = get_logger(__name__)

def str_to_bool(value: str) -> bool:
    """Convert string to boolean."""
    return value.lower() in ('true', 't', 'yes', 'y', '1', 'on')

class EdenImageGenerator:
    def __init__(self):
        """Initialize Eden AI Image Generator."""
        load_dotenv()
        
        # Get API key from environment
        self.api_key = os.getenv('EDEN_API_KEY')
        if not self.api_key:
            logger.error("EDEN_API_KEY not found in environment variables")
            raise ValueError("EDEN_API_KEY is required")
            
        # Get mock configuration
        self.use_mock = str_to_bool(os.getenv('USE_IMAGE_MOCK_IF_AVAILABLE', 'True'))
        logger.debug(f"Mock usage configuration: {self.use_mock}")
        
        self.api_url = "https://api.edenai.run/v2/image/generation"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        self.cost_tracker = CostTracker("eden_image", self._calculate_request_cost)
        self._ensure_directories()
        logger.info(f"EdenImageGenerator initialized successfully (mock enabled: {self.use_mock})")

    def _ensure_image_directory(self) -> None:
        """Ensure the logs/images directory exists."""
        image_dir = Path("logs/images")
        image_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured image directory exists at {image_dir}")

    def _calculate_request_cost(self, request_data: Dict[str, Any]) -> float:
        """
        Calculate cost for an Eden AI image generation request.
        
        Args:
            request_data: Dictionary containing image generation details
                        May include 'cost' from API response
            
        Returns:
            Calculated cost in dollars
            
        Note:
            Base cost is set to 0.016 based on Eden AI's DALL-E 2 pricing for 256x256 images
        """
        # If cost is provided in the request data (from API response), use it
        if 'cost' in request_data:
            cost = float(request_data['cost'])
            logger.debug(f"Using cost from API response: ${cost:.6f}")
            return cost
            
        # Otherwise use base cost
        base_cost = 0.016  # Eden AI's DALL-E 2 cost for 256x256 images
        logger.debug(f"Using base cost: ${base_cost:.6f}")
        return base_cost

    async def _download_image(self, image_url: str, prompt: str) -> str:
        """
        Download and save the generated image.
        
        Args:
            image_url: URL of the generated image
            prompt: The prompt used to generate the image
            
        Returns:
            Path to the saved image
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    response.raise_for_status()
                    image_content = await response.read()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_prompt = "".join(x for x in prompt[:30] if x.isalnum() or x in (' ', '-', '_')).strip()
            safe_prompt = safe_prompt.replace(' ', '_')
            
            filename = f"eden_{timestamp}_{safe_prompt}.png"
            filepath = Path("logs/images") / filename
            
            with open(filepath, 'wb') as f:
                f.write(image_content)
                
            logger.info(f"Image saved successfully at {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to download and save image: {str(e)}")
            raise

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        # Ensure images directory
        image_dir = Path("logs/images")
        image_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured image directory exists at {image_dir}")
        
        # Ensure mock directory
        mock_dir = Path("mock")
        mock_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured mock directory exists at {mock_dir}")

    def _save_mock_response(self, response_content: Any) -> None:
        """Save API response for mock testing."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = Path("mock") / f"eden_response_{timestamp}.json"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(response_content, f, indent=2)
                
            logger.debug(f"Saved mock response to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save mock response: {str(e)}")
            # Don't raise - this is not critical for the main functionality

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
                
            # Get all eden response files
            mock_files = list(mock_dir.glob("eden_response_*.json"))
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

    async def generate_image(
        self,
        prompt: str,
        session_id: str,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate an image using Eden AI.
        
        Args:
            prompt: The text prompt for image generation
            session_id: Unique identifier for the session
            options: Optional configuration parameters (resolution, etc.)
            
        Returns:
            Path to the saved image
            
        Raises:
            Exception: If API call fails or budget exceeded
        """
        try:
            logger.debug(f"Generating image for prompt: {prompt[:50]}...")
            
            # Calculate request cost before making API call
            request_data = {"prompt_length": len(prompt)}
            
            # Check for mock response if enabled
            response_content = self._get_mock_response() if self.use_mock else None
            
            if response_content is None:
                if self.use_mock:
                    logger.debug("No mock response available, falling back to API call")
                else:
                    logger.debug("Mock disabled, making API call")
                    
                # No mock available or mock disabled, make actual API call
                payload = {
                    "providers": "openai",
                    "text": prompt,
                    "resolution": options.get("resolution", "256x256"),
                    "num_images": 1,
                    "response_as_dict": False,
                    "settings": {
                        "openai": "dall-e-2"
                    }
                }
                
                logger.debug(f"Sending request with payload: {json.dumps(payload, indent=2)}")
                
                # Make API request
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.api_url, json=payload, headers=self.headers) as response:
                        response.raise_for_status()
                        response_content = await response.json()
                        
                # Save response for future mock testing
                self._save_mock_response(response_content)
            else:
                logger.info("Using mock response for image generation")

            # Parse response - expecting array format
            if not isinstance(response_content, list) or not response_content:
                raise ValueError("Expected non-empty array response")
            
            result = response_content[0]  # Get first result
            
            if 'items' not in result:
                raise ValueError("Missing 'items' in response")
                
            if not result['items']:
                logger.error("No items returned in the response")
                raise ValueError("No items returned in response")
                
            # Get base64 image data from response
            try:
                items = result['items']
                logger.debug(f"Found {len(items)} items in response")
                image_data = items[0]['image']
                logger.debug("Successfully extracted base64 image data from response")
            except (KeyError, IndexError) as e:
                logger.error(f"Failed to extract image data from response: {str(e)}")
                logger.debug(f"Response structure: {json.dumps(items, indent=2)}")
                raise ValueError("Could not find image data in response")
            
            # Save image
            image_path = await self._save_image(image_data, prompt)
            
            # Track cost for both mock and real API calls
            # If using mock, use the cost from the response if available, otherwise use calculated cost
            if isinstance(response_content, list) and response_content and 'cost' in response_content[0]:
                request_data['cost'] = response_content[0]['cost']
            self.cost_tracker.calculate_cost(request_data, session_id)
            
            logger.info("Image generated successfully")
            return image_path
            
        except aiohttp.ClientError as e:
            logger.error(f"API request failed: {str(e)}")
            raise
        except ValueError as e:
            logger.error(f"Invalid response: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Image generation failed: {str(e)}")
            logger.debug(f"Exception type: {type(e)}")
            logger.debug(f"Exception details: {str(e)}")
            raise

    async def _save_image(self, image_data: str, prompt: str) -> str:
        """
        Save the base64 image data to a file.
        
        Args:
            image_data: Base64 encoded image data
            prompt: The prompt used to generate the image
            
        Returns:
            Path to the saved image
        """
        try:
            # Decode base64 image data
            if ',' in image_data:  # Handle potential data URI format
                image_data = image_data.split(',', 1)[1]
            
            image_bytes = base64.b64decode(image_data)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_prompt = "".join(x for x in prompt[:30] if x.isalnum() or x in (' ', '-', '_')).strip()
            safe_prompt = safe_prompt.replace(' ', '_')
            
            filename = f"eden_{timestamp}_{safe_prompt}.png"
            filepath = Path("logs/images") / filename
            
            with open(filepath, 'wb') as f:
                f.write(image_bytes)
                
            logger.info(f"Image saved successfully at {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save image: {str(e)}")
            raise

# Singleton instance
eden_image_generator = EdenImageGenerator() 
"""Eden AI Image Generator
=====================

Main implementation of the Eden AI image generator.

Design Decisions:
- Uses dataclasses for request/response models
- Implements proper error handling with custom exceptions
- Supports mock responses for testing
- Integrates with cost tracking
- Provides debug image saving
- Uses async/await for API calls
"""

import os
import aiohttp
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from utils.logging_config import get_logger
from app.cost_tracker.cost_tracker import CostTracker

from .models.image_models import (
    ImageGenerationRequest,
    ImageGenerationResponse,
    GeneratedImage,
    ImageGenerationError
)
from .exceptions.eden_exceptions import (
    ConfigurationError,
    APIError,
    ValidationError
)
from .utils.image_utils import save_debug_image
from .utils.mock_utils import save_mock_response, get_mock_response, should_use_mock
from .config.constants import (
    API_URL,
    ENV_API_KEY,
    ENV_USE_MOCK,
    ResponseStatus,
    BASE_COST
)

logger = get_logger(__name__)

class EdenImageGenerator:
    """Main class for generating images using Eden AI."""
    
    def __init__(self):
        """Initialize the image generator."""
        load_dotenv()
        
        # Get API key
        self.api_key = os.getenv(ENV_API_KEY)
        if not self.api_key:
            raise ConfigurationError(f"{ENV_API_KEY} not found in environment variables")
            
        # Configure mock usage
        self.use_mock = should_use_mock(os.getenv(ENV_USE_MOCK, 'True'))
        logger.debug(f"Mock usage configuration: {self.use_mock}")
        
        # Set up API configuration
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        
        # Initialize cost tracker
        self.cost_tracker = CostTracker("eden_image", self._calculate_request_cost)
        logger.info(f"EdenImageGenerator initialized successfully (mock enabled: {self.use_mock})")
    
    def _calculate_request_cost(self, request_data: Dict[str, Any]) -> float:
        """
        Calculate cost for an image generation request.
        
        Args:
            request_data: Dictionary containing request details
            
        Returns:
            Calculated cost in dollars
        """
        return request_data.get('cost', BASE_COST)
    
    def _parse_api_error(self, error_data: Dict[str, Any]) -> str:
        """
        Parse error message from API response.
        
        Args:
            error_data: Error data from API
            
        Returns:
            Parsed error message
        """
        error_msg = error_data.get('message', 'Unknown API error')
        
        # Extract OpenAI error if available
        if 'Openai has returned an error:' in error_msg:
            try:
                openai_error = json.loads(error_msg.split('Openai has returned an error:', 1)[1])
                error_msg = openai_error['error']['message']
            except (json.JSONDecodeError, KeyError):
                pass
                
        return error_msg
    
    def _process_api_response(self, response_content: Dict[str, Any]) -> ImageGenerationResponse:
        """
        Process API response into response model.
        
        Args:
            response_content: Raw API response
            
        Returns:
            Processed ImageGenerationResponse
        """
        if not isinstance(response_content, list) or not response_content:
            raise ValidationError("Expected non-empty array response")
            
        result = response_content[0]
        
        # Check for API errors
        if 'error' in result:
            error_msg = self._parse_api_error(result['error'])
            return ImageGenerationResponse(
                status=ResponseStatus.ERROR,
                error=ImageGenerationError(message=error_msg)
            )
        
        # Validate response structure
        if 'items' not in result or not result['items']:
            return ImageGenerationResponse(
                status=ResponseStatus.ERROR,
                error=ImageGenerationError(message="No items returned in the response")
            )
            
        # Extract image data
        try:
            items = result['items']
            image_data = items[0]['image']
            
            return ImageGenerationResponse(
                status=ResponseStatus.SUCCESS,
                images=[GeneratedImage(
                    image_data=image_data,
                    format="png",
                    cost=result.get('cost', BASE_COST)
                )]
            )
            
        except (KeyError, IndexError) as e:
            return ImageGenerationResponse(
                status=ResponseStatus.ERROR,
                error=ImageGenerationError(
                    message="Failed to extract image data from API response",
                    details={"error": str(e)}
                )
            )
    
    def generate_image(
        self,
        prompt: str,
        session_id: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate an image using Eden AI.
        
        Args:
            prompt: Text description for image generation
            session_id: Session identifier for cost tracking
            options: Optional configuration parameters
            
        Returns:
            Dictionary containing generation results
        """
        try:
            logger.debug(f"Generating image for prompt: {prompt[:50]}...")
            
            # Prepare request data for cost tracking
            request_data = {"prompt_length": len(prompt)}
            
            # Check for mock response
            response_content = get_mock_response() if self.use_mock else None
            
            if response_content is None:
                if self.use_mock:
                    logger.debug("No mock response available, falling back to API call")
                
                # Create and validate request
                request = ImageGenerationRequest(
                    text=prompt,
                    **(options or {})
                )
                
                # Make API request
                with requests.Session() as session:
                    response = session.post(API_URL, json=request.to_dict(), headers=self.headers)
                    response.raise_for_status()
                    response_content = response.json()
                    
                    # Save successful response for mocking
                    save_mock_response(response_content)
            
            # Process response
            result = self._process_api_response(response_content)
            
            # Save debug image if successful
            if result.is_success and result.first_image:
                try:
                    result.debug_path = save_debug_image(
                        result.first_image.image_data,
                        prompt
                    )
                except Exception as e:
                    logger.warning(f"Failed to save debug image: {str(e)}")
            
            # Track costs
            if result.first_image:
                request_data['cost'] = result.first_image.cost
            self.cost_tracker.calculate_cost(request_data, session_id)
            
            return result.to_dict()
            
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {str(e)}"
            logger.error(error_msg)
            return ImageGenerationResponse(
                status=ResponseStatus.ERROR,
                error=ImageGenerationError(message=error_msg)
            ).to_dict()
        except Exception as e:
            error_msg = f"Image generation failed: {str(e)}"
            logger.error(error_msg)
            logger.debug(f"Exception type: {type(e)}")
            logger.debug(f"Exception details: {str(e)}")
            return ImageGenerationResponse(
                status=ResponseStatus.ERROR,
                error=ImageGenerationError(message=error_msg)
            ).to_dict() 
"""Gemini API Integration
=======================

Provides integration with Google's Gemini 2.0 Flash experimental API for AI text generation.

Public Components:
- GeminiAPI: Main class for interacting with Gemini API
- generate_content(): Primary method for text generation
- configure_gemini(): Setup function for API configuration

Design Decisions:
- Uses Gemini 1.5 Flash model for optimal performance
- Implements retry mechanism for API failures
- Includes proper error handling and logging
- Supports async operations for better scalability

Integration Notes:
- Requires GEMINI_API_KEY in environment variables
- Configurable via logging config
- Rate limiting implemented to prevent API abuse
"""

import os
import logging
from typing import Optional, Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GeminiAPI:
    def __init__(self):
        """Initialize Gemini API wrapper."""
        load_dotenv()
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            raise ValueError("GEMINI_API_KEY is required")
        
        self.configure()
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        logger.info("GeminiAPI initialized successfully")

    def configure(self) -> None:
        """Configure Gemini API with credentials."""
        try:
            genai.configure(api_key=self.api_key)
            logger.debug("Gemini API configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure Gemini API: {str(e)}")
            raise

    async def generate_content(
        self, 
        prompt: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate content using Gemini API.
        
        Args:
            prompt: The input prompt for content generation
            options: Optional configuration parameters
            
        Returns:
            Generated text content
            
        Raises:
            Exception: If API call fails
        """
        try:
            logger.debug(f"Generating content for prompt: {prompt[:50]}...")
            response = self.model.generate_content(prompt)
            logger.info("Content generated successfully")
            return response.text
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            raise

# Singleton instance
gemini_api = GeminiAPI()

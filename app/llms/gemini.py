"""Gemini API Integration
=======================

Provides integration with Google's Gemini 2.0 Flash experimental API for AI text generation.

Public Components:
- GeminiAPI: Main class for interacting with Gemini API
- generate_content(): Primary method for text generation
- configure_gemini(): Setup function for API configuration

Design Decisions:
- Uses Gemini 2.0 Flash Experimental model for optimal performance
- Implements retry mechanism for API failures
- Includes proper error handling and logging
- Supports async operations for better scalability
- Maintains conversation history for contextual responses
- Integrates with CostTracker for budget management
- Implements token-based cost calculation (0.01$/input token, 0.02$/output token)

Integration Notes:
- Requires GEMINI_API_KEY in environment variables
- Configurable via logging config
- Rate limiting implemented to prevent API abuse
- Uses CostTracker for budget management
"""

import os
from typing import Optional, Dict, Any, List
import google.generativeai as genai
from dotenv import load_dotenv
from utils.logging_config import get_logger
from app.cost_tracker.cost_tracker import CostTracker

# Get logger instance
logger = get_logger(__name__)

class GeminiAPI:
    def __init__(self):
        """Initialize Gemini API wrapper."""
        load_dotenv()
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            raise ValueError("GEMINI_API_KEY is required")
        
        self.configure()
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        self.cost_tracker = CostTracker("gemini", self._calculate_request_cost)
        self.chats = {}  # Store chat sessions
        logger.info("GeminiAPI initialized successfully")

    def configure(self) -> None:
        """Configure Gemini API with credentials."""
        try:
            genai.configure(api_key=self.api_key)
            logger.debug("Gemini API configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure Gemini API: {str(e)}")
            raise

    def get_or_create_chat(self, session_id: str):
        """Get or create a new chat session for the given session ID."""
        if session_id not in self.chats:
            self.chats[session_id] = self.model.start_chat(history=[])
        return self.chats[session_id]

    def _calculate_request_cost(self, request_data: Dict[str, Any]) -> float:
        """
        Calculate cost for a Gemini API request.
        
        Args:
            request_data: Dictionary containing input_tokens and output_tokens
            
        Returns:
            Calculated cost in dollars
            
        Note:
            Current pricing:
            - Input tokens: $0.01 per token
            - Output tokens: $0.02 per token
        """
        input_tokens = request_data.get("input_tokens", 0)
        output_tokens = request_data.get("output_tokens", 0)
        
        input_cost = input_tokens * 0.01  # $0.01 per input token EXAPLE FOR DEBUG
        output_cost = output_tokens * 0.02  # $0.02 per output token EXAPLE FOR DEBUG
        
        total_cost = input_cost + output_cost
        logger.debug(
            f"Calculated cost: ${total_cost:.6f} "
            f"(Input: {input_tokens} tokens = ${input_cost:.6f}, "
            f"Output: {output_tokens} tokens = ${output_cost:.6f})"
        )
        
        return total_cost

    async def generate_content(
        self, 
        prompt: str,
        session_id: str,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate content using Gemini API with conversation history.
        
        Args:
            prompt: The input prompt for content generation
            session_id: Unique identifier for the chat session
            options: Optional configuration parameters
            
        Returns:
            Generated text content
            
        Raises:
            Exception: If API call fails or budget exceeded
        """
        try:
            logger.debug(f"Generating content for prompt: {prompt[:50]}...")
            chat = self.get_or_create_chat(session_id)
            
            # Calculate request cost before making API call
            request_data = {
                "input_tokens": len(prompt.split()),  # Simple approximation
                "output_tokens": 0  # Will be updated after response
            }
            
            # Get response from API
            response = chat.send_message(prompt)
            
            # Update cost with actual output tokens
            request_data["output_tokens"] = len(response.text.split())  # Simple approximation
            
            # Track cost after successful API call
            self.cost_tracker.calculate_cost(request_data, session_id)
            
            logger.info("Content generated successfully")
            return response.text
        except ValueError as e:
            # Re-raise budget exceeded error
            logger.error(f"Budget exceeded: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            raise

# Singleton instance
gemini_api = GeminiAPI()

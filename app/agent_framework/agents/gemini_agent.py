"""Gemini Agent Integration
=======================

Provides integration with Google's Gemini 2.0 Flash experimental API using SmolAgents for advanced interactions.

Public Components:
- GeminiAgent: Main class for agent-based interactions with Gemini API
- generate_content(): Primary method for agent-based text generation

Design Decisions:
- Inherits from BaseAgent for standardized agent interface
- Uses SmolAgents ToolCallingAgent for structured interactions
- Maintains chat history per session for context
- Supports multiple tools including image generation and research
- Implements cost tracking per session
- Uses standardized response format

Integration Notes:
- Requires GEMINI_API_KEY in environment variables
- Uses CostTracker for budget management
- Integrates with Eden AI for image generation
- Compatible with existing chat UI structure
"""

from typing import Optional, Dict, Any, List
from smolagents.agents import ToolCallingAgent

from app.agent_framework.agents.base_agent import BaseAgent, AgentConfig, AgentType
from app.agent_framework.agents.agent_utils import (
    format_chat_history,
    calculate_tokens,
    extract_final_answer,
    format_agent_flow,
    AgentResponse
)
from app.agent_framework.tools.audio_generation.tool import AudioGenerationTool
from app.agent_framework.tools.image_generation.tool import ImageGenerationTool
from app.agent_framework.tools.research.tool import ResearchTool
from utils.logging_config import get_logger

logger = get_logger(__name__)

class GeminiAgent(BaseAgent):
    """Agent implementation using Google's Gemini API."""
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize Gemini Agent.
        
        Args:
            session_id: Unique identifier for the session
        """
        config = AgentConfig(
            agent_type=AgentType.GEMINI,
            required_env_vars=['GEMINI_API_KEY']
        )
        super().__init__(session_id, config)
        
        self.chat_histories: Dict[str, List[Dict[str, str]]] = {}
        self.agent_flows: Dict[str, AgentResponse] = {}
        self.session_artifacts: Dict[str, List[Any]] = {}
        
        self.configure()

    def configure(self) -> None:
        """Configure agent with necessary tools and setup."""
        try:
            # Initialize session artifacts if needed
            if self.session_id not in self.session_artifacts:
                self.session_artifacts[self.session_id] = []
            logger.debug("Gemini Agent configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure Gemini Agent: {str(e)}")
            raise

    def _create_agent(self) -> ToolCallingAgent:
        """Create a new agent instance with all necessary tools."""
        if self.session_artifacts.get(self.session_id) is None:
            raise RuntimeError("Session artifacts not initialized. Call configure() first.")
            
        return ToolCallingAgent(
            tools=[
                ImageGenerationTool(
                    session_id=self.session_id,
                    artifacts=self.session_artifacts[self.session_id]
                ),
                ResearchTool(
                    session_id=self.session_id,
                    artifacts=self.session_artifacts[self.session_id]
                ),
                AudioGenerationTool(
                    session_id=self.session_id,
                    artifacts=self.session_artifacts[self.session_id]
                )
            ],
            model=self.model
        )

    async def generate_content(self, prompt: str) -> str:
        """
        Generate content using Gemini API with agent-based processing.
        
        Args:
            prompt: The input prompt for content generation
            
        Returns:
            Generated text content (final answer from agent)
            
        Raises:
            Exception: If API call fails or budget exceeded
        """
        try:
            logger.debug(f"Generating content for prompt: {prompt[:50]}...")
            agent = self._create_agent()
            
            # Calculate request cost
            request_data = {
                "input_tokens": calculate_tokens(prompt),
                "output_tokens": 0
            }
            
            # Format chat history for context
            history = self.chat_histories.get(self.session_id, [])
            context = format_chat_history(history) if history else ""
            
            # Combine history and current prompt
            full_prompt = f"{context}\n\nUser: {prompt}" if context else prompt
            
            # Get response from agent
            response = agent.run(full_prompt)
            final_answer = extract_final_answer(response)
            
            # Format and store agent flow
            execution_trace = getattr(response, 'execution_trace', [])
            self.agent_flows[self.session_id] = format_agent_flow(execution_trace)
            self.agent_flows[self.session_id]['final_answer'] = final_answer
            
            # Update chat history
            self.chat_histories.setdefault(self.session_id, []).append({
                "user": prompt,
                "assistant": final_answer
            })
            
            # Update cost with actual output tokens
            request_data["output_tokens"] = calculate_tokens(final_answer)
            self.cost_tracker.calculate_cost(request_data, self.session_id)
            
            logger.info("Content generated successfully")
            return final_answer
        except ValueError as e:
            logger.error(f"Budget exceeded: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            raise

    def get_agent_flow(self, session_id: str) -> Optional[AgentResponse]:
        """
        Get the full agent interaction flow for a session.
        
        Args:
            session_id: The session ID to get the flow for
            
        Returns:
            The full agent interaction flow or None if not found
        """
        return self.agent_flows.get(session_id)

    def get_chat_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get the chat history for a session.
        
        Args:
            session_id: The session ID to get history for
            
        Returns:
            List of chat messages for the session
        """
        return self.chat_histories.get(session_id, [])

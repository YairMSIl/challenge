"""Gemini Agent Integration
=======================

Provides integration with Google's Gemini 2.0 Flash experimental API using SmolAgents for advanced interactions.

Public Components:
- GeminiAPIAgent: Main class for agent-based interactions with Gemini API
- generate_content(): Primary method for agent-based text generation
- configure_gemini(): Setup function for API configuration

Design Decisions:
- Uses SmolAgents ToolCallingAgent for structured interactions
- Maintains compatibility with existing GeminiAPI interface
- Captures both final answers and full agent interaction flow
- Integrates with CostTracker for budget management
- Uses LiteLLMModel for Gemini integration
- Implements token-based cost calculation
- Maintains chat history per session for context
- Formats chat history for agent consumption
- Supports image generation through Eden AI integration

Integration Notes:
- Requires GEMINI_API_KEY in environment variables
- Configurable via logging config
- Uses CostTracker for budget management
- Compatible with existing chat UI structure
- Integrates with Eden AI for image generation
"""

import os
from typing import Optional, Dict, Any, List, Tuple
from dotenv import load_dotenv
from smolagents.agents import ToolCallingAgent
from smolagents import tool, LiteLLMModel
from app.agent_framework.tools.aiml_audio_generator_tool import AIMLAudioGeneratorTool
from app.models.artifact import Artifact
from utils.logging_config import get_logger
from app.cost_tracker.cost_tracker import CostTracker
from app.agent_framework.tools.generate_image_eden_ai import EdenImageGenerationTool
from app.agent_framework.tools.research_tool import ResearchTool

# Get logger instance
logger = get_logger(__name__)

class GeminiAPIAgent:
    def __init__(self):
        """Initialize Gemini API Agent wrapper."""
        load_dotenv()
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            raise ValueError("GEMINI_API_KEY is required")
        
        self.configure()
        self.cost_tracker = CostTracker("gemini", self._calculate_request_cost)
        self.agent_sessions = {}  # Store agent sessions
        self.chat_histories = {}  # Store chat histories per session
        self.session_artifacts = {} # Stores anything internal tools have created for reference
        logger.info("GeminiAPIAgent initialized successfully")

    def configure(self) -> None:
        """Configure Gemini API with credentials."""
        try:
            # Initialize with LiteLLMModel using Gemini
            self.model = LiteLLMModel(
                model_id="gemini/gemini-2.0-flash-exp",
                api_key=self.api_key
            )
            logger.debug("Gemini API configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure Gemini API: {str(e)}")
            raise

    def get_or_create_agent(self, session_id: str) -> ToolCallingAgent:
        """Get or create a new agent session for the given session ID."""
        if session_id not in self.agent_sessions:
            self.session_artifacts[session_id] = []
            
            # Create agent with tools including image generation and research
            self.agent_sessions[session_id] = ToolCallingAgent(
                tools=[
                    EdenImageGenerationTool(session_id, artifacts=self.session_artifacts[session_id]),
                    ResearchTool(session_id=session_id),  # Pass session_id to ResearchTool
                    AIMLAudioGeneratorTool(session_id=session_id, artifacts=self.session_artifacts[session_id])
                ],
                model=self.model,
            )
            # Initialize chat history for this session
            self.chat_histories[session_id] = []
        return self.agent_sessions[session_id]

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
        
        input_cost = input_tokens * 0.01  # $0.01 per input token
        output_cost = output_tokens * 0.02  # $0.02 per output token
        
        total_cost = input_cost + output_cost
        logger.debug(
            f"Calculated cost: ${total_cost:.6f} "
            f"(Input: {input_tokens} tokens = ${input_cost:.6f}, "
            f"Output: {output_tokens} tokens = ${output_cost:.6f})"
        )
        
        return total_cost

    def _format_chat_history(self, history: List[Dict[str, str]]) -> str:
        """Format chat history for agent consumption."""
        formatted = []
        for entry in history:
            formatted.extend([
                f"User: {entry['user']}",
                f"Assistant: {entry['assistant']}"
            ])
        return "\n".join(formatted)

    async def generate_content(
        self, 
        prompt: str,
        session_id: str,
    ) -> str:
        """
        Generate content using Gemini API with agent-based processing.
        
        Args:
            prompt: The input prompt for content generation
            session_id: Unique identifier for the agent session
            
        Returns:
            Generated text content (final answer from agent)
            
        Raises:
            Exception: If API call fails or budget exceeded
        """
        try:
            logger.debug(f"Generating content with agent for prompt: {prompt[:50]}...")
            agent = self.get_or_create_agent(session_id)
            
            # Calculate request cost before making API call
            request_data = {
                "input_tokens": len(prompt.split()),  # Simple approximation
                "output_tokens": 0  # Will be updated after response
            }
            
            # Format chat history for context
            history = self.chat_histories.get(session_id, [])
            context = self._format_chat_history(history) if history else ""
            
            # Combine history and current prompt
            full_prompt = f"{context}\n\nUser: {prompt}" if context else prompt
            
            # Get response from agent
            response = agent.run(full_prompt)
            
            # Extract final answer and agent flow information
            final_answer = str(response)  # SmolAgents returns AgentText which converts to string
            
            # Get the agent's execution trace
            execution_trace = getattr(response, 'execution_trace', [])
            
            # Format the agent flow
            agent_flow = {
                'tool_calls': [],
                'internal_messages': [],
                'final_answer': final_answer,
            }
            
            # Process execution trace
            for step in execution_trace:
                if hasattr(step, 'tool_call'):
                    # Add tool call information
                    tool_call = {
                        'name': step.tool_call.name,
                        'parameters': step.tool_call.parameters,
                        'result': step.tool_call.result if hasattr(step.tool_call, 'result') else None
                    }
                    agent_flow['tool_calls'].append(tool_call)
                
                if hasattr(step, 'message'):
                    # Add internal thought process/messages
                    agent_flow['internal_messages'].append(str(step.message))
            
            # Update chat history
            self.chat_histories[session_id].append({
                "user": prompt,
                "assistant": final_answer
            })
            
            # Update cost with actual output tokens
            request_data["output_tokens"] = len(str(response).split())  # Simple approximation
            
            # Track cost after successful API call
            self.cost_tracker.calculate_cost(request_data, session_id)
            
            # Store full flow in session for later retrieval
            if not hasattr(self, 'agent_flows'):
                self.agent_flows = {}
            self.agent_flows[session_id] = agent_flow
            
            logger.info("Content generated successfully with agent")
            return final_answer
        except ValueError as e:
            # Re-raise budget exceeded error
            logger.error(f"Budget exceeded: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            raise

    def _extract_final_answer(self, agent_response: Dict[str, Any]) -> str:
        """Extract the final answer from the agent's response."""
        # This implementation depends on the exact structure of your agent's response
        # Modify according to your needs
        if isinstance(agent_response, dict):
            return agent_response.get('final_answer', str(agent_response))
        return str(agent_response)

    def get_agent_flow(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the full agent interaction flow for a session.
        
        Args:
            session_id: The session ID to get the flow for
            
        Returns:
            The full agent interaction flow or None if not found
        """
        return getattr(self, 'agent_flows', {}).get(session_id)

    def get_chat_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get the chat history for a session.
        
        Args:
            session_id: The session ID to get history for
            
        Returns:
            List of chat history entries
        """
        return self.chat_histories.get(session_id, [])

# Singleton instance
gemini_agent_api = GeminiAPIAgent() 
"""Agent Utilities
===============

Utility functions and constants used across different agent implementations.

Public Components:
- format_chat_history: Format chat history for agent consumption
- calculate_tokens: Simple token count estimation
- AgentResponse: Type for standardized agent responses

Design Decisions:
- Centralized utility functions to avoid code duplication
- Simple token estimation for cost calculation
- Standardized response format
- Type hints for better code maintainability

Integration Notes:
- Used by all agent implementations
- Provides common formatting and calculation functions
- Implements standard logging patterns
"""

from typing import List, Dict, Any, TypedDict
from utils.logging_config import get_logger

logger = get_logger(__name__)

class AgentResponse(TypedDict):
    """Standardized response format for agent outputs."""
    final_answer: str
    tool_calls: List[Dict[str, Any]]
    internal_messages: List[str]

def format_chat_history(history: List[Dict[str, str]]) -> str:
    """
    Format chat history for agent consumption.
    
    Args:
        history: List of chat messages with 'user' and 'assistant' keys
        
    Returns:
        Formatted chat history as string
    """
    formatted = []
    for entry in history:
        formatted.extend([
            f"User: {entry['user']}",
            f"Assistant: {entry['assistant']}"
        ])
    return "\n".join(formatted)

def calculate_tokens(text: str) -> int:
    """
    Simple token count estimation.
    
    Args:
        text: Input text to estimate tokens for
        
    Returns:
        Estimated token count
        
    Note:
        This is a simple approximation. For production,
        consider using a proper tokenizer.
    """
    # Simple approximation: split on whitespace
    return len(text.split())

def extract_final_answer(agent_response: Any) -> str:
    """
    Extract final answer from agent response.
    
    Args:
        agent_response: Raw agent response
        
    Returns:
        Extracted final answer as string
    """
    if isinstance(agent_response, dict):
        return agent_response.get('final_answer', str(agent_response))
    return str(agent_response)

def format_agent_flow(execution_trace: List[Any]) -> AgentResponse:
    """
    Format agent execution trace into standardized response.
    
    Args:
        execution_trace: Raw execution trace from agent
        
    Returns:
        Formatted AgentResponse
    """
    agent_flow: AgentResponse = {
        'tool_calls': [],
        'internal_messages': [],
        'final_answer': ''
    }
    
    for step in execution_trace:
        if hasattr(step, 'tool_call'):
            tool_call = {
                'name': step.tool_call.name,
                'parameters': step.tool_call.parameters,
                'result': getattr(step.tool_call, 'result', None)
            }
            agent_flow['tool_calls'].append(tool_call)
        
        if hasattr(step, 'message'):
            agent_flow['internal_messages'].append(str(step.message))
    
    return agent_flow 
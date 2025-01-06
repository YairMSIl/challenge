"""Base Agent Framework
===================

Provides the foundation for all agent implementations in the system.

Public Components:
- BaseAgent: Abstract base class for all agents
- AgentType: Enum for different types of agents
- AgentConfig: Configuration dataclass
- CostConfig: Cost calculation configuration

Design Decisions:
- Abstract base class pattern for consistent agent interface
- Standardized cost tracking and session management
- Common configuration and initialization patterns
- Type-safe implementation with proper error handling
- Modular design for easy extension

Integration Notes:
- Requires proper environment configuration
- Uses CostTracker for budget management
- Implements standard logging patterns
- Requires concrete implementations for abstract methods
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Any, Optional, List
import os
import uuid
from dotenv import load_dotenv
from smolagents import LiteLLMModel
from smolagents.agents import ToolCallingAgent

from utils.logging_config import get_logger
from app.cost_tracker.cost_tracker import CostTracker

logger = get_logger(__name__)

class AgentType(Enum):
    """Enum defining different types of agents in the system."""
    GEMINI = auto()
    RESEARCH = auto()

@dataclass
class CostConfig:
    """Configuration for cost calculation."""
    input_token_cost: float = 0.01  # Cost per input token
    output_token_cost: float = 0.02  # Cost per output token

@dataclass
class AgentConfig:
    """Configuration for agent initialization."""
    agent_type: AgentType
    model_name: str = "gemini/gemini-2.0-flash-exp"
    required_env_vars: List[str] = None
    session_id_min_length: int = 8
    session_id_max_length: int = 32

    def __post_init__(self):
        if self.required_env_vars is None:
            self.required_env_vars = ['GEMINI_API_KEY']

class BaseAgent(ABC):
    """Abstract base class for all agents in the system."""
    
    def __init__(self, session_id: Optional[str], config: AgentConfig):
        """
        Initialize base agent with common functionality.
        
        Args:
            session_id: Unique identifier for the session
            config: Agent configuration
            
        Raises:
            ValueError: If session_id format is invalid
        """
        self.config = config
        self.session_id = session_id or self._generate_session_id()
        
        if not self._is_valid_session_id(self.session_id):
            raise ValueError(
                f"Invalid session ID format. Must be alphanumeric and "
                f"between {config.session_id_min_length}-{config.session_id_max_length} characters."
            )
        
        self.cost_config = CostConfig()
        
        # Load environment variables
        load_dotenv()
        self._validate_env_vars()
        
        # Initialize components
        self.model = self._initialize_model()
        self.cost_tracker = CostTracker(
            str(config.agent_type).lower(),
            self._calculate_request_cost
        )
        
        logger.info(f"{config.agent_type} agent initialized for session {self.session_id}")

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return str(uuid.uuid4()).replace('-', '')[:self.config.session_id_max_length]

    def _is_valid_session_id(self, session_id: str) -> bool:
        """
        Validate session ID format.
        
        Args:
            session_id: Session ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        return (
            isinstance(session_id, str) and
            session_id.isalnum() and
            self.config.session_id_min_length <= len(session_id) <= self.config.session_id_max_length
        )

    def _validate_env_vars(self) -> None:
        """
        Validate required environment variables are present.
        
        Raises:
            ValueError: If any required environment variable is missing
        """
        missing_vars = [
            var for var in self.config.required_env_vars 
            if not os.getenv(var)
        ]
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def _initialize_model(self) -> LiteLLMModel:
        """
        Initialize the LLM model.
        
        Returns:
            Initialized LiteLLMModel instance
            
        Raises:
            Exception: If model initialization fails
        """
        try:
            return LiteLLMModel(
                model_id=self.config.model_name,
                api_key=os.getenv('GEMINI_API_KEY')
            )
        except Exception as e:
            logger.error(f"Failed to initialize model: {str(e)}")
            raise

    def _calculate_request_cost(self, request_data: Dict[str, Any]) -> float:
        """
        Calculate cost for an API request.
        
        Args:
            request_data: Dictionary containing input_tokens and output_tokens
            
        Returns:
            Calculated cost in dollars
        """
        input_tokens = request_data.get("input_tokens", 0)
        output_tokens = request_data.get("output_tokens", 0)
        
        input_cost = input_tokens * self.cost_config.input_token_cost
        output_cost = output_tokens * self.cost_config.output_token_cost
        
        total_cost = input_cost + output_cost
        logger.debug(
            f"Calculated cost: ${total_cost:.6f} "
            f"(Input: {input_tokens} tokens = ${input_cost:.6f}, "
            f"Output: {output_tokens} tokens = ${output_cost:.6f})"
        )
        
        return total_cost

    @abstractmethod
    def configure(self) -> None:
        """Configure the agent with necessary setup."""
        pass

    @abstractmethod
    def _create_agent(self) -> ToolCallingAgent:
        """Create a new agent instance with appropriate tools."""
        pass 
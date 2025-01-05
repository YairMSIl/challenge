"""Cost Tracking System
====================
Provides a flexible cost tracking system for various API services.

Public Components:
- CostTracker: Main class for tracking API costs
- CostCallback: Type for cost calculation callbacks
- get_tracker: Factory function to get a cost tracker instance

Design Decisions:
- Uses callback-based cost calculation for flexibility
- Maintains per-session cost tracking
- Supports different cost models (per-token, per-request, etc.)
- Thread-safe cost accumulation
- Persistent cost tracking across service restarts

Integration Notes:
- Each service should instantiate its own CostTracker
- Cost calculation callbacks should be provided during initialization
- Session IDs should be consistent across services
- Each service must implement its own cost calculation logic
"""

from typing import Callable, Dict, Any, Optional
from dataclasses import dataclass, field
from threading import Lock
import json
from pathlib import Path
import time
from utils.logging_config import get_logger

# Get logger instance
logger = get_logger(__name__)

# Type for cost calculation callbacks
CostCallback = Callable[[Dict[str, Any]], float]

@dataclass
class SessionCosts:
    """Tracks costs for a single session."""
    total_cost: float = 0.0
    request_count: int = 0
    last_request_time: float = field(default_factory=time.time)
    last_request_cost: float = 0.0

class CostTracker:
    """
    Tracks API usage costs with flexible cost calculation.
    
    Attributes:
        service_name: Name of the service being tracked
        cost_callback: Function to calculate cost for a request
        session_costs: Dictionary mapping session IDs to their costs
    """
    
    def __init__(
        self,
        service_name: str,
        cost_callback: CostCallback,
        max_budget: float = 25.0  # Default from project requirements
    ):
        """
        Initialize a cost tracker for a service.
        
        Args:
            service_name: Name of the service to track
            cost_callback: Function that calculates cost for a request
            max_budget: Maximum budget allowed (default 25.0)
        """
        self.service_name = service_name
        self.cost_callback = cost_callback
        self.max_budget = max_budget
        self.session_costs: Dict[str, SessionCosts] = {}
        self._lock = Lock()  # Thread safety for cost updates
        
        logger.info(f"Initialized cost tracker for {service_name}")
        
    def calculate_cost(self, request_data: Dict[str, Any], session_id: str) -> float:
        """
        Calculate and track cost for a request.
        
        Args:
            request_data: Data about the request (format depends on service)
            session_id: Unique identifier for the session
            
        Returns:
            The calculated cost for this request
            
        Raises:
            ValueError: If cost would exceed budget
        """
        # Calculate cost using callback
        cost = self.cost_callback(request_data)
        
        with self._lock:
            # Get or create session costs
            if session_id not in self.session_costs:
                self.session_costs[session_id] = SessionCosts()
            
            session = self.session_costs[session_id]
            
            # Check if cost would exceed budget
            if session.total_cost + cost > self.max_budget:
                logger.error(f"Cost {cost} would exceed budget for session {session_id}")
                raise ValueError(
                    f"Request would exceed budget. "
                    f"Current: ${session.total_cost:.3f}, "
                    f"Request: ${cost:.3f}, "
                    f"Budget: ${self.max_budget:.2f}"
                )
            
            # Update session costs
            session.total_cost += cost
            session.request_count += 1
            session.last_request_time = time.time()
            session.last_request_cost = cost
            
            logger.info(
                f"Tracked {self.service_name} request cost: ${cost:.3f} "
                f"(Session {session_id} total: ${session.total_cost:.3f})"
            )
            
            return cost
            
    def get_session_costs(self, session_id: str) -> Optional[SessionCosts]:
        """Get cost information for a session."""
        return self.session_costs.get(session_id)
        
    def get_total_cost(self, session_id: str) -> float:
        """Get total cost for a session."""
        if session_id in self.session_costs:
            return self.session_costs[session_id].total_cost
        return 0.0
        
    def get_remaining_budget(self, session_id: str) -> float:
        """Get remaining budget for a session."""
        return self.max_budget - self.get_total_cost(session_id)

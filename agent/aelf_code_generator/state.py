"""
This module defines the state types for the AELF smart contract code generation workflow.
"""

from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage

class InternalState(TypedDict, total=False):
    """
    Internal state fields that should not appear in the UI.
    These fields are populated by the nodes during processing.
    """
    user_requirements: Optional[Dict[str, Any]]  # Extracted requirements from text
    contract_type: Optional[str]  # Type of contract
    contract_features: Optional[List[str]]  # List of features
    contract_methods: Optional[List[Dict[str, Any]]]  # Method specifications
    state_variables: Optional[List[Dict[str, Any]]]  # State variable definitions
    contract_events: Optional[List[Dict[str, Any]]]  # Event definitions
    generated_code: Optional[str]  # Generated contract code
    generation_logs: Optional[List[str]]  # Generation process logs
    is_complete: Optional[bool]  # Whether generation is complete

class AgentState(TypedDict):
    """
    State type for the agent workflow.
    Only exposes messages for conversation history.
    All other state is handled internally by the nodes.
    """
    messages: List[BaseMessage]  # List of conversation messages

# State key mappings for internal use
STATE_KEYS = {
    "user_requirements": "user_requirements",
    "contract_type": "contract_type",
    "contract_features": "contract_features",
    "contract_methods": "contract_methods",
    "state_variables": "state_variables",
    "contract_events": "contract_events",
    "generated_code": "generated_code",
    "generation_logs": "generation_logs",
    "is_complete": "is_complete"
} 
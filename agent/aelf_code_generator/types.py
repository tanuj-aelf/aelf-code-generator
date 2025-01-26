"""
This module defines shared type definitions.
"""

from typing import TypedDict, Dict

class AgentState(TypedDict):
    """State type for the agent workflow."""
    input: str  # Original dApp description
    output: Dict[str, str]  # Generated outputs

def get_default_state() -> AgentState:
    """Initialize default state."""
    return {
        "input": "",
        "output": {
            "contract": "",
            "state": "",
            "proto": "",
            "analysis": ""
        }
    } 
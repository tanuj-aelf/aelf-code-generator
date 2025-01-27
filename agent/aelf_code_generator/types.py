"""
This module defines the state types for the AELF code generator agent.
"""

from typing import TypedDict

class ContractOutput(TypedDict):
    """
    Represents the generated smart contract components
    """
    contract: str
    state: str
    proto: str
    analysis: str

class AgentState(TypedDict):
    """State type for the agent workflow."""
    input: str  # Original dApp description
    output: ContractOutput  # Generated outputs

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
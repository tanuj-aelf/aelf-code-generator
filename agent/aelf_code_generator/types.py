"""
This module defines the state types for the AELF code generator agent.
"""

from typing import TypedDict, List, Optional, NotRequired

class CodebaseInsight(TypedDict, total=False):
    """
    Represents insights gathered from analyzing sample codebases
    """
    project_structure: str
    coding_patterns: str
    relevant_samples: List[str]
    implementation_guidelines: str

class ContractOutput(TypedDict, total=False):
    """
    Represents the generated smart contract components
    """
    contract: str  # Main contract implementation
    state: str    # State class implementation
    proto: str    # Protobuf definitions
    reference: str  # Contract references
    project: str   # Project configuration
    analysis: str  # Requirements analysis

class InternalState(TypedDict, total=False):
    """Internal state for agent workflow."""
    analysis: str
    codebase_insights: CodebaseInsight
    output: ContractOutput

class AgentState(TypedDict, total=False):
    """State type for the agent workflow."""
    input: str  # Original dApp description
    _internal: NotRequired[InternalState]  # Internal state management (not shown in UI)

def get_default_state() -> AgentState:
    """Initialize default state."""
    return {
        "input": ""
    } 
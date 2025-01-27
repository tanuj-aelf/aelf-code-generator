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

class CodeFile(TypedDict):
    """
    Represents a code file with its content and metadata
    """
    content: str  # The actual code content
    file_type: str  # File type (e.g., "csharp", "proto", "xml")
    path: str  # Path in project structure (e.g., "src/ContractName.cs")

class ContractOutput(TypedDict, total=False):
    """
    Represents the generated smart contract components
    """
    contract: CodeFile  # Main contract implementation
    state: CodeFile    # State class implementation
    proto: CodeFile    # Protobuf definitions
    reference: CodeFile  # Contract references
    project: CodeFile   # Project configuration
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
"""
This module defines the state types for the AELF code generator agent.
"""

from typing import TypedDict, List, Optional, NotRequired, Dict, Literal

class CodebaseInsight(TypedDict, total=False):
    """
    Represents insights gathered from analyzing sample codebases
    """
    project_structure: str
    coding_patterns: str
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
    metadata: List[CodeFile]  # Additional files generated by LLM
    analysis: str  # Requirements analysis

class InternalState(TypedDict, total=False):
    """Internal state for agent workflow."""
    analysis: str
    codebase_insights: CodebaseInsight
    output: ContractOutput
    validation_count: int
    validation_result: str
    fixes: str  # Store validation feedback for next iteration
    validation_complete: bool

class AgentState(TypedDict, total=False):
    """State type for the agent workflow."""
    input: str  # Original dApp description
    generate: NotRequired[Dict[Literal["_internal"], InternalState]]  # Internal state management wrapped in generate

def get_default_state() -> AgentState:
    """Initialize default state."""
    empty_code_file = {
        "content": "",
        "file_type": "",
        "path": ""
    }
    
    return {
        "input": "",
        "generate": {
            "_internal": {
                "analysis": "",
                "codebase_insights": {
                    "project_structure": "",
                    "coding_patterns": "",
                    "implementation_guidelines": ""
                },
                "output": {
                    "contract": empty_code_file,
                    "state": empty_code_file,
                    "proto": empty_code_file,
                    "reference": empty_code_file,
                    "project": empty_code_file,
                    "metadata": [],
                    "analysis": ""
                },
                "validation_count": 0
            }
        }
    } 
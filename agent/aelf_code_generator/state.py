"""
This module defines the state management for the AELF smart contract code generator agent.
"""

from typing import List, TypedDict, Optional
from langgraph.graph import MessagesState

class ContractTemplate(TypedDict):
    """Represents a smart contract template."""
    name: str
    description: str
    features: List[str]
    source_path: str
    code: str

class GithubResource(TypedDict):
    """Represents a GitHub resource from the AELF samples repository."""
    url: str
    title: str
    description: str
    content: Optional[str]

class CodeFeedback(TypedDict):
    """Represents feedback on the generated code."""
    improvements: List[str]
    security_issues: List[str]
    gas_optimizations: List[str]
    missing_features: List[str]
    suggestions: List[str]

class Log(TypedDict):
    """Represents a log of an action performed by the agent."""
    message: str
    done: bool

class AgentState(MessagesState):
    """
    State management for the AELF smart contract code generator agent.
    """
    model: str
    user_requirements: Optional[str]  # User's description of the desired smart contract
    contract_type: Optional[str]  # Type of contract (e.g., "lottery", "crowdfunding")
    contract_features: List[str]  # Specific features requested by user
    contract_patterns: List[str]  # Identified patterns from analysis
    selected_template: Optional[ContractTemplate]
    generated_contract: Optional[str]
    github_resources: List[GithubResource]
    improvement_feedback: Optional[CodeFeedback]  # Feedback for code improvements
    iteration_count: int  # Track number of improvement iterations
    logs: List[Log] 
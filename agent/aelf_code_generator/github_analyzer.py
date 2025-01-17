"""
This module handles analyzing GitHub repositories for smart contract examples.
"""

from typing import cast, Dict
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from copilotkit.langchain import copilotkit_customize_config
from aelf_code_generator.state import AgentState
from aelf_code_generator.model import get_model

def initialize_analyzer_state(state: AgentState) -> AgentState:
    """Initialize state with required fields for GitHub analysis."""
    if "github_analysis" not in state:
        state["github_analysis"] = ""
    if "user_requirements" not in state:
        state["user_requirements"] = ""
    if "contract_type" not in state:
        state["contract_type"] = ""
    if "contract_features" not in state:
        state["contract_features"] = []
    return state

async def github_analyzer_node(state: AgentState, config: RunnableConfig) -> AgentState:
    """
    Analyzes GitHub repositories for relevant smart contract examples.
    """
    # Initialize state
    state = initialize_analyzer_state(state)
    
    config = copilotkit_customize_config(
        config,
        emit_intermediate_state=[{
            "state_key": "github_analysis",
            "tool": "AnalyzeGitHub",
            "tool_argument": "query",
        }],
    )

    model = get_model(state)
    
    # Create the search query using the requirements
    search_query = (
        f"site:github.com/AElfProject/aelf-samples smart contract {state['user_requirements']}"
        if state.get("user_requirements")
        else "site:github.com/AElfProject/aelf-samples smart contract examples"
    )

    # Add contract type if available
    if state.get("contract_type"):
        search_query += f" type:{state['contract_type']}"

    # Add features if available
    if state.get("contract_features"):
        features_str = " ".join(state["contract_features"])
        search_query += f" features:{features_str}"

    messages = [
        HumanMessage(
            content=f"""Analyze the following GitHub search query for AELF smart contract examples:
            {search_query}
            
            Look for:
            1. Similar contract implementations
            2. Relevant code patterns
            3. Best practices
            4. Common pitfalls to avoid
            
            Focus on examples that match the user's requirements:
            - Contract Type: {state.get('contract_type', 'Not specified')}
            - Features: {', '.join(state.get('contract_features', ['Not specified']))}
            """
        )
    ]

    response = await model.ainvoke(messages, config)
    ai_message = cast(AIMessage, response)
    
    # Update state with analysis
    state["github_analysis"] = ai_message.content
    
    return state 
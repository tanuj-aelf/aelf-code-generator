"""
This module defines the main agent workflow for AELF smart contract code generation.
"""

from typing import TypedDict, Annotated, Sequence, cast
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.checkpoint.memory import MemorySaver
from aelf_code_generator.state import AgentState
from aelf_code_generator.chat import chat_node
from aelf_code_generator.github_analyzer import github_analyzer_node
from aelf_code_generator.code_generator import code_generator_node

def create_agent() -> StateGraph:
    """
    Creates the agent workflow graph for AELF smart contract code generation.
    
    Flow:
    1. Chat -> Get requirements
    2. Contract Analyzer -> Analyze requirements and find examples
    3. Code Generator -> Generate code
    """
    # Initialize the workflow graph
    workflow = StateGraph(AgentState)

    # Add nodes to the graph
    workflow.add_node("chat", chat_node)
    workflow.add_node("contract_analyzer", contract_analyzer)
    workflow.add_node("code_generator", code_generator_node)

    # Define linear flow
    workflow.add_edge("chat", "contract_analyzer")
    workflow.add_edge("contract_analyzer", "code_generator")
    
    # Set the entry point
    workflow.set_entry_point("chat")

    # Add conditional edge to end
    workflow.add_conditional_edges(
        "code_generator",
        lambda x: "__end__" if x.get("is_complete", False) else "chat"
    )

    return workflow

async def contract_analyzer(state: AgentState, config: dict) -> AgentState:
    """
    Analyzes the contract requirements and updates the state with analysis results.
    """
    # Initialize required state fields
    if "github_analysis" not in state:
        state["github_analysis"] = ""
    if "is_complete" not in state:
        state["is_complete"] = False
        
    # Run GitHub analysis
    state = await github_analyzer_node(state, config)
    
    return state

# Create and compile the graph with memory
memory = MemorySaver()
workflow = create_agent()
graph = workflow.compile(checkpointer=memory)

# Export the graph for use in other modules
__all__ = ["graph"] 
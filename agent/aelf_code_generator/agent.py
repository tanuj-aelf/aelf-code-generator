"""
This module defines the main agent workflow for AELF smart contract code generation.
"""

from typing import TypedDict, Dict, List, Any, Annotated, Optional
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
from aelf_code_generator.state import InternalState, STATE_KEYS
from aelf_code_generator.chat import chat_node
from aelf_code_generator.github_analyzer import github_analyzer_node
from aelf_code_generator.code_generator import code_generator_node

class AgentState(TypedDict):
    """State type for the agent workflow."""
    messages: Annotated[List[BaseMessage], add_messages]  # List of conversation messages

def create_agent():
    """Create the agent workflow."""
    # Define the workflow graph
    workflow = StateGraph(AgentState)

    # Add nodes to the graph
    workflow.add_node("chat", chat_node)
    workflow.add_node("contract_analyzer", github_analyzer_node)
    workflow.add_node("code_generator", code_generator_node)

    # Set entry point to chat
    workflow.set_entry_point("chat")

    # Define linear flow
    workflow.add_edge("chat", "contract_analyzer")
    workflow.add_edge("contract_analyzer", "code_generator")
    workflow.add_edge("code_generator", END)

    # Create and compile the graph with memory
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)

# Create the graph
graph = create_agent()

# Export the graph
__all__ = ["graph"] 
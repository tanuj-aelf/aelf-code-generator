"""
This module defines the main agent workflow for AELF smart contract code generation.
"""

from typing import TypedDict, Dict, List, Any, Annotated, Union
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
from aelf_code_generator.state import InternalState
from aelf_code_generator.input_node import input_node
from aelf_code_generator.chat import chat_node
from aelf_code_generator.github_analyzer import github_analyzer_node
from aelf_code_generator.code_generator import code_generator_node

class AgentState(TypedDict):
    """State type for the agent workflow."""
    messages: List[BaseMessage]  # List of conversation messages

def create_agent():
    """Create the agent workflow."""
    # Define the workflow graph with text input
    workflow = StateGraph(AgentState)

    # Add nodes to the graph
    workflow.add_node("input", input_node)  # Text input node
    workflow.add_node("chat", chat_node)  # Analysis node
    workflow.add_node("contract_analyzer", github_analyzer_node)
    workflow.add_node("code_generator", code_generator_node)

    # Set entry point to input node with text input
    workflow.set_entry_point("input")

    # Define linear flow
    workflow.add_edge("input", "chat")  # Input -> Chat
    workflow.add_edge("chat", "contract_analyzer")  # Chat -> Analysis
    workflow.add_edge("contract_analyzer", "code_generator")  # Analysis -> Generation
    workflow.add_edge("code_generator", END)  # Generation -> End

    # Create and compile the graph with memory
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)

# Create the graph
graph = create_agent()

# Export the graph
__all__ = ["graph"] 
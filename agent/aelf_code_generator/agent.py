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
from aelf_code_generator.template_selector import template_selector_node
from aelf_code_generator.code_generator import code_generator_node
from aelf_code_generator.review_code import review_code_node

def create_agent() -> StateGraph:
    """
    Creates the agent workflow graph for AELF smart contract code generation.
    
    Flow:
    1. Chat -> Get requirements
    2. Contract Analyzer -> Analyze requirements and find examples
    3. Template Selector -> Select appropriate template
    4. Code Generator -> Generate initial code
    5. Review Code -> Review and suggest improvements
    6. Either:
       - Go back to Code Generator for improvements
       - Go back to Chat for major requirement changes
       - End if code is satisfactory
    """
    # Initialize the workflow graph
    workflow = StateGraph(AgentState)

    # Add nodes to the graph
    workflow.add_node("chat", chat_node)
    workflow.add_node("contract_analyzer", contract_analyzer)
    workflow.add_node("template_selector", template_selector_node)
    workflow.add_node("code_generator", code_generator_node)
    workflow.add_node("review_code", review_code_node)

    # Define main flow
    workflow.add_edge("chat", "contract_analyzer")
    workflow.add_edge("contract_analyzer", "template_selector")
    workflow.add_edge("template_selector", "code_generator")
    workflow.add_edge("code_generator", "review_code")
    
    # Add essential feedback loops
    workflow.add_edge("review_code", "code_generator")  # For code improvements
    workflow.add_edge("review_code", "chat")  # For major requirement changes
    
    # Set the entry point
    workflow.set_entry_point("chat")

    # Add conditional edges to end
    workflow.add_conditional_edges(
        "review_code",
        lambda x: "end" if x.get("is_complete", False) else (
            "chat" if x.get("needs_requirements_update", False) else "code_generator"
        )
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
    if "needs_requirements_update" not in state:
        state["needs_requirements_update"] = False
        
    # Run GitHub analysis
    state = await github_analyzer_node(state, config)
    
    return state

# Create and compile the graph with memory
memory = MemorySaver()
workflow = create_agent()
graph = workflow.compile(checkpointer=memory)

# Export the graph for use in other modules
__all__ = ["graph"] 
"""
This module defines the requirement collector node for gathering initial smart contract requirements.
"""

from typing import Dict, Any, Literal, Optional, TypedDict, Annotated
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from pydantic import BaseModel, Field

class RequirementInput(BaseModel):
    """Input schema for the requirement collector node."""
    text: str = Field(
        description="Describe your smart contract requirements in plain text",
        examples=[
            "I need a voting contract where users can create proposals and vote",
            "Create an NFT marketplace with listing and bidding features",
            "Token contract with mint, burn, and transfer functions",
            "DAO governance contract with proposal voting and treasury management"
        ]
    )

async def requirement_collector_node(
    state: Dict[str, Any],
    config: RunnableConfig
) -> Command[Literal["chat"]]:
    """
    Collects initial requirements from user input and prepares the state for chat.
    
    Args:
        state: Current workflow state
        config: Configuration for the runnable
    """
    # Initialize messages list if not present
    if "messages" not in state:
        state["messages"] = []
    
    # Get input from state
    input_data = state.get("input")
    if input_data and hasattr(input_data, "text"):
        message = HumanMessage(content=input_data.text)
        state["messages"].append(message)
    
    # Always proceed to chat node
    return Command(goto="chat", update=state)

# Export the node
__all__ = ["requirement_collector_node", "RequirementInput"] 
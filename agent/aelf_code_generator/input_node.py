"""
This module handles the initial text input for dApp description.
"""

from typing import Dict, Any, Literal
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from aelf_code_generator.validation import validate_input

INITIAL_PROMPT = """Describe your dApp requirements in plain text. For example:
- "I need a voting contract where users can create proposals and vote"
- "Create an NFT marketplace with listing and bidding features"
- "Token contract with mint, burn, and transfer functions"
- "DAO governance contract with proposal voting and treasury management"
"""

async def input_node(state: Dict[str, Any], config: RunnableConfig) -> Command[Literal["chat"]]:
    """
    Input node for collecting dApp description.
    Only handles text input and forwards to chat node.
    """
    # Initialize messages if not present
    if "messages" not in state:
        state["messages"] = []

    # Get and validate input
    input_data = config.get("input", "")
    try:
        if input_data:
            clean_input = validate_input(input_data)
            # Add the message to history
            state["messages"].append(
                HumanMessage(content=clean_input)
            )
            # Forward to chat node
            return Command(
                goto="chat",
                update={
                    "messages": state["messages"]
                }
            )
    except ValueError as e:
        return Command(
            goto="input",
            update={
                "messages": [
                    HumanMessage(content=str(e))
                ]
            }
        )

    # If no input, show initial prompt
    return Command(
        goto="input",
        update={
            "messages": [
                HumanMessage(content=INITIAL_PROMPT)
            ]
        }
    ) 
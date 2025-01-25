"""
This module handles user interactions to gather smart contract requirements.
"""

from typing import cast, Literal, List, Dict, Optional, Any
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from pydantic import BaseModel, Field
from aelf_code_generator.state import AgentState, STATE_KEYS
from aelf_code_generator.model import get_model
from aelf_code_generator.text_to_contract import extract_requirements
from aelf_code_generator.models import ContractRequirements
import json

SYSTEM_PROMPT = """You are an AELF smart contract assistant. Your task is to analyze the user's dApp description and provide helpful insights.

When analyzing the description, consider:
- Main functionality and goals
- User interaction patterns
- Business logic requirements
- Security requirements
- Access control needs

Respond in natural language:
1. Confirm your understanding of the requirements
2. Ask clarifying questions if needed
3. Explain any assumptions you're making
4. Suggest standard features that might be helpful

Example response:
"I understand you need a token contract with mint and transfer capabilities. I'll assume standard ERC20-like behavior including:
- Minting restricted to owner/admin
- Transfer between any addresses
- Balance tracking
- Approval mechanism

Would you like to add any custom features or modify these assumptions?"

Keep the conversation natural and avoid technical jargon unless necessary."""

async def chat_node(state: Dict[str, Any], config: RunnableConfig) -> Command[Literal["contract_analyzer", "chat"]]:
    """
    Chat node for processing dApp description and generating requirements.
    Extracts requirements from the text description and updates internal state.
    """
    # Get the latest message
    latest_message = state["messages"][-1] if state["messages"] else None
    if not latest_message:
        return Command(
            goto="chat",
            update=state
        )

    # Extract requirements from the text and store in internal state
    if isinstance(latest_message, HumanMessage):
        requirements = await extract_requirements(latest_message.content, state)
        state[STATE_KEYS["user_requirements"]] = requirements.dict()

    # Prepare message history
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *state["messages"]
    ]

    # Get model response without tools
    model = get_model(state)
    response = await model.ainvoke(messages, tools=[])  # Explicitly disable tools
    ai_message = cast(AIMessage, response)

    # Update state with response
    state["messages"] = state["messages"] + [ai_message]

    # Move to analyzer once we have requirements
    if STATE_KEYS["user_requirements"] in state:
        return Command(
            goto="contract_analyzer",
            update=state
        )
    
    # Stay in chat if we need more information
    return Command(
        goto="chat",
        update=state
    ) 
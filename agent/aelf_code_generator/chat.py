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

If any key information is missing, make reasonable assumptions based on common patterns and best practices. For example:
- For token contracts: assume ERC20-like behavior
- For NFT contracts: assume ERC721-like behavior
- For governance: assume standard proposal/voting mechanisms
- For marketplaces: assume basic listing/buying/selling features

Respond in natural language:
1. Confirm your understanding of the requirements
2. List any assumptions you're making
3. Highlight any potential security considerations
4. Suggest standard features that might be helpful

Keep the conversation natural and avoid technical jargon unless necessary."""

def initialize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """Initialize all required state fields."""
    if "messages" not in state:
        state["messages"] = []
    
    # Initialize all internal state fields
    state[STATE_KEYS["user_requirements"]] = None
    state[STATE_KEYS["contract_type"]] = None
    state[STATE_KEYS["contract_features"]] = []
    state[STATE_KEYS["contract_methods"]] = []
    state[STATE_KEYS["state_variables"]] = []
    state[STATE_KEYS["contract_events"]] = []
    state[STATE_KEYS["generated_code"]] = None
    state[STATE_KEYS["generation_logs"]] = []
    state[STATE_KEYS["is_complete"]] = False
    
    return state

async def chat_node(state: Dict[str, Any], config: RunnableConfig) -> Command[Literal["contract_analyzer", "chat"]]:
    """
    Chat node for processing dApp description and generating requirements.
    Extracts requirements from the text description and updates internal state.
    """
    # Initialize state
    state = initialize_state(state)
    
    # Get the latest message
    latest_message = state["messages"][-1] if state["messages"] else None
    if not latest_message:
        return Command(goto="chat", update=state)

    try:
        # Get model response first to understand requirements better
        messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
        model = get_model(state)
        response = await model.ainvoke(messages, tools=[])
        ai_message = cast(AIMessage, response)
        
        # Extract requirements from both user input and AI analysis
        if isinstance(latest_message, HumanMessage):
            combined_input = f"{latest_message.content}\n\nAI Analysis:\n{ai_message.content}"
            requirements = await extract_requirements(combined_input, state)
            
            # Update state with requirements and AI message
            state[STATE_KEYS["user_requirements"]] = requirements
            state["messages"].append(ai_message)
            
            # Move to analyzer
            return Command(goto="contract_analyzer", update=state)
        
    except Exception as e:
        # If requirements extraction fails, continue chat with error message
        error_message = AIMessage(content=f"I need more details to understand your requirements. Could you please provide more information about:\n- The main purpose of your smart contract\n- Key features and functionality needed\n- Any specific business rules or constraints")
        state["messages"].append(error_message)
    
    # Stay in chat if we need more information
    return Command(goto="chat", update=state) 
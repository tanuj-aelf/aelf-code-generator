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
import json

SYSTEM_PROMPT = """You are an AELF smart contract assistant. Your task is to analyze the user's dApp description and extract structured requirements.

When analyzing the description, consider:
- Main functionality and goals
- User interaction patterns
- Business logic requirements
- Security requirements
- Access control needs

If any key information is missing, make reasonable assumptions based on common patterns and best practices. For example:
- For token contracts: assume ERC20-like behavior with mint, burn, transfer
- For NFT contracts: assume ERC721-like behavior with minting, transfers, approvals
- For governance: assume standard proposal/voting mechanisms with quorum and timelock
- For marketplaces: assume basic listing/buying/selling with escrow

Your output should be a JSON object with the following structure:
{
    "contract_type": "token|nft|governance|marketplace|etc",
    "contract_features": ["feature1", "feature2", ...],
    "contract_methods": [
        {
            "name": "method_name",
            "description": "what the method does",
            "parameters": [{"name": "param1", "type": "type1"}],
            "returns": {"type": "return_type"},
            "access": "public|owner_only|role_based"
        }
    ],
    "state_variables": [
        {
            "name": "variable_name",
            "type": "variable_type",
            "description": "what this stores"
        }
    ],
    "contract_events": [
        {
            "name": "event_name",
            "description": "when this is emitted",
            "parameters": [{"name": "param1", "type": "type1"}]
        }
    ]
}"""

async def extract_requirements(text: str, model) -> Dict[str, Any]:
    """Extract structured requirements from text using LLM."""
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Please analyze this smart contract description and provide structured requirements:\n\n{text}")
    ]
    
    response = await model.ainvoke(messages)
    ai_message = cast(AIMessage, response)
    
    # Extract JSON from response
    try:
        # Find JSON block in the response
        json_text = ai_message.content
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0]
        elif "```" in json_text:
            json_text = json_text.split("```")[1].split("```")[0]
            
        requirements = json.loads(json_text)
        return requirements
    except Exception as e:
        raise ValueError(f"Failed to parse requirements: {str(e)}")

async def chat_node(state: Dict[str, Any], config: RunnableConfig) -> Command[Literal["contract_analyzer", "chat"]]:
    """
    Chat node for processing dApp description and generating requirements.
    Extracts structured requirements from the text description.
    """
    # Initialize state if needed
    if "messages" not in state:
        state["messages"] = []
        return Command(goto="chat", update=state)

    # Get the latest message
    latest_message = state["messages"][-1] if state["messages"] else None
    if not latest_message or not isinstance(latest_message, HumanMessage):
        return Command(goto="chat", update=state)

    try:
        # Get model for requirements extraction
        model = get_model(state)
        
        # Extract requirements
        requirements = await extract_requirements(latest_message.content, model)
        
        # Update state with structured requirements
        state.update({
            "user_requirements": requirements,
            "contract_type": requirements["contract_type"],
            "contract_features": requirements["contract_features"],
            "contract_methods": requirements["contract_methods"],
            "state_variables": requirements["state_variables"],
            "contract_events": requirements["contract_events"],
            "generated_code": None,
            "generation_logs": [],
            "is_complete": False
        })
        
        # Add AI confirmation message
        confirmation = (
            f"I understand you want a {requirements['contract_type']} contract with the following features:\n"
            + "\n".join(f"- {feature}" for feature in requirements["contract_features"])
            + "\n\nI'll generate the appropriate AELF smart contract code."
        )
        state["messages"].append(AIMessage(content=confirmation))
        
        # Move to analyzer
        return Command(goto="contract_analyzer", update=state)
        
    except Exception as e:
        # If requirements extraction fails, ask for clarification
        error_message = AIMessage(content=(
            "I need more details to understand your requirements. Could you please provide more information about:\n"
            "- The main purpose of your smart contract\n"
            "- Key features and functionality needed\n"
            "- Any specific business rules or constraints"
        ))
        state["messages"].append(error_message)
        return Command(goto="chat", update=state)

# Export the node
__all__ = ["chat_node"] 
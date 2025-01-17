"""
This module handles user interactions to gather smart contract requirements.
"""

from typing import cast, Literal, List, Dict
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain.tools import tool
from langgraph.types import Command
from copilotkit.langchain import copilotkit_customize_config
from pydantic import BaseModel, Field
from aelf_code_generator.state import AgentState
from aelf_code_generator.model import get_model

SYSTEM_PROMPT = """You are an AELF smart contract generation assistant. Help users define their smart contract requirements.
Extract key information about the type of contract they want (e.g., lottery, crowdfunding, NFT marketplace).
Identify specific features and requirements they mention.

Available contract types from AELF samples:
- Lottery Game
- Simple DAO
- NFT Sale
- Expense Tracker
- Staking
- Tic-tac-toe
- Todo List
- Vote
- Allowance

Ask clarifying questions if the requirements are unclear.
Once requirements are clear, use the ProcessRequirements tool to structure them with:
- description: Detailed description of what the contract should do
- type: The type of contract from the available types
- features: List of specific features requested"""

class RequirementsInput(BaseModel):
    """Input schema for processing contract requirements."""
    description: str = Field(
        description="Detailed description of the smart contract requirements"
    )
    type: str = Field(
        description="Type of the smart contract (e.g., lottery, crowdfunding, etc.)"
    )
    features: List[str] = Field(
        description="List of specific features requested for the contract"
    )

@tool
def ProcessRequirements(requirements: RequirementsInput) -> Dict:
    """Process and structure the user's smart contract requirements."""
    return {
        "description": requirements.description,
        "type": requirements.type,
        "features": requirements.features
    }

def initialize_state(state: AgentState) -> AgentState:
    """Initialize state with default values if not already present."""
    if "user_requirements" not in state:
        state["user_requirements"] = ""
    if "contract_type" not in state:
        state["contract_type"] = ""
    if "contract_features" not in state:
        state["contract_features"] = []
    if "messages" not in state:
        state["messages"] = []
    return state

async def chat_node(state: AgentState, config: RunnableConfig) -> Command[Literal["contract_analyzer", "chat", "__end__"]]:
    """
    Chat node for gathering and processing user requirements for smart contract generation.
    """
    # Initialize state with default values
    state = initialize_state(state)
    
    config = copilotkit_customize_config(
        config,
        emit_intermediate_state=[{
            "state_key": "user_requirements",
            "tool": "ProcessRequirements",
            "tool_argument": "requirements",
        }],
    )

    model = get_model(state)
    
    # Prepare message history for Gemini
    messages = []
    if state["messages"]:
        for msg in state["messages"]:
            if isinstance(msg, HumanMessage):
                messages.append(msg)
            elif isinstance(msg, AIMessage):
                messages.append(msg)
            # Skip other message types that Gemini doesn't support
    
    # Add system prompt as a prefix to the first message if there are messages
    if messages:
        first_msg = messages[0]
        if isinstance(first_msg, HumanMessage):
            messages[0] = HumanMessage(content=f"{SYSTEM_PROMPT}\n\nUser: {first_msg.content}")
    else:
        # If no messages, start with system prompt
        messages = [HumanMessage(content=SYSTEM_PROMPT)]

    response = await model.bind_tools(
        [ProcessRequirements],
    ).ainvoke(messages, config)

    ai_message = cast(AIMessage, response)
    
    # If the AI is asking clarifying questions, continue chat
    if not ai_message.tool_calls:
        state["messages"].append(ai_message)
        return Command(
            goto="chat",
            update={"messages": state["messages"]}
        )

    try:
        # Get the tool call arguments
        tool_args = ai_message.tool_calls[0]["args"]
        
        # Handle different response formats
        if isinstance(tool_args, str):
            import json
            tool_args = json.loads(tool_args)
        
        # Extract requirements based on the structure
        if "requirements" in tool_args:
            requirements = tool_args["requirements"]
        else:
            requirements = tool_args
            
        # Convert to dict if it's a Pydantic model
        if hasattr(requirements, "dict"):
            requirements = requirements.dict()
        elif isinstance(requirements, str):
            requirements = json.loads(requirements)
            
        # Ensure we have a dictionary with the required fields
        if not isinstance(requirements, dict):
            raise ValueError(f"Invalid requirements format: {type(requirements)}")
            
        # Update state with requirements, using safe get operations
        state["user_requirements"] = (
            requirements.get("description", "") 
            if isinstance(requirements, dict) 
            else str(requirements)
        )
        state["contract_type"] = (
            requirements.get("type", "") 
            if isinstance(requirements, dict) 
            else ""
        )
        state["contract_features"] = (
            requirements.get("features", []) 
            if isinstance(requirements, dict) 
            else []
        )
        
        state["messages"].append(ai_message)
        state["messages"].append(ToolMessage(
            tool_call_id=ai_message.tool_calls[0]["id"],
            content="Requirements processed successfully."
        ))

        return Command(
            goto="contract_analyzer",
            update=state
        )
        
    except Exception as e:
        # If there's any error processing the requirements, continue the chat
        error_message = HumanMessage(
            content="I apologize, but I couldn't process those requirements properly. Could you please provide more details about what kind of smart contract you need?"
        )
        state["messages"].append(error_message)
        return Command(
            goto="chat",
            update=state
        ) 
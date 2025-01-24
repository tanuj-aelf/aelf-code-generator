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
import json

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
    
    # Prepare message history
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    
    if state["messages"]:
        messages.extend(state["messages"])

    model = get_model(state)
    
    # Bind the ProcessRequirements tool and get response
    response = await model.bind_tools(
        [ProcessRequirements],
    ).ainvoke(messages)

    ai_message = cast(AIMessage, response)
    
    # Update messages list with AI's response
    updated_messages = state["messages"] + [ai_message]
    
    # If no tool calls, continue chat
    if not ai_message.tool_calls:
        return Command(
            goto="chat",
            update={"messages": updated_messages}
        )

    try:
        tool_call = ai_message.tool_calls[0]
        
        # Parse tool arguments
        if isinstance(tool_call["args"], str):
            tool_args = json.loads(tool_call["args"])
        else:
            tool_args = tool_call["args"]
            
        # Ensure we have the requirements structure
        if isinstance(tool_args, dict):
            if "requirements" in tool_args:
                requirements = tool_args["requirements"]
            else:
                requirements = tool_args
        else:
            raise ValueError("Invalid tool arguments format")
            
        # Convert Pydantic model to dict if needed
        if hasattr(requirements, "dict"):
            requirements = requirements.dict()
            
        # Validate requirements structure
        if not all(key in requirements for key in ["description", "type", "features"]):
            raise ValueError("Missing required fields in requirements")
            
        # Create tool message
        tool_message = ToolMessage(
            tool_call_id=tool_call["id"],
            content="Requirements processed successfully."
        )
        
        # Update state atomically with all fields
        return Command(
            goto="contract_analyzer",
            update={
                "messages": updated_messages + [tool_message],
                "user_requirements": requirements["description"],
                "contract_type": requirements["type"],
                "contract_features": requirements["features"]
            }
        )
        
    except Exception as e:
        print(f"Error processing requirements: {str(e)}")
        error_message = HumanMessage(
            content=f"I couldn't process the requirements properly. Please provide more specific details about your smart contract needs. Error: {str(e)}"
        )
        return Command(
            goto="chat",
            update={"messages": updated_messages + [error_message]}
        ) 
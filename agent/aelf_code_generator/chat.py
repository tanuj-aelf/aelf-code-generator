"""
This module handles user interactions to gather smart contract requirements.
"""

from typing import cast, Literal, List, Dict, Optional
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain.tools import tool
from langgraph.types import Command
from pydantic import BaseModel, Field
from aelf_code_generator.state import AgentState
from aelf_code_generator.model import get_model
import json

SYSTEM_PROMPT = """You are an AELF smart contract generation assistant. Help users define their smart contract requirements.
Analyze the requirements carefully to understand the contract's purpose, features, and technical needs.

When analyzing smart contract requirements, extract:
1. Core Contract Purpose:
   - Main functionality and goals
   - User interaction flows
   - Access control model

2. Contract Methods:
   For each method, identify:
   - Method name (in PascalCase)
   - Purpose and description
   - Input parameters with their types
   - Return value type and structure
   - Required permissions/roles
   - State changes it makes
   - Events it should emit
   - Validation rules

3. Contract State:
   For each state variable:
   - Variable name and type
   - Purpose and usage
   - Access patterns
   - Mapping relationships

4. Events:
   For each event:
   - Event name (in PascalCase)
   - Parameters to include
   - When it should be emitted

5. Technical Requirements:
   - Performance considerations
   - Security requirements
   - Error handling needs

Structure the requirements systematically to enable proper code generation.
Be specific and detailed in method specifications to ensure proper code generation."""

# Define nested models for better type safety
class MethodParameter(BaseModel):
    """Parameter specification for a method."""
    name: str = Field(description="Parameter name")
    type: str = Field(description="Parameter type")
    description: str = Field(description="Parameter description")

class MethodReturn(BaseModel):
    """Return value specification for a method."""
    type: str = Field(description="Return type")
    description: str = Field(description="Return value description")

class StateVariable(BaseModel):
    """State variable specification."""
    name: str = Field(description="Variable name")
    type: str = Field(description="Variable type")
    description: str = Field(description="Variable description")
    is_mapping: bool = Field(description="Whether this is a mapping type", default=False)

class EventParameter(BaseModel):
    """Event parameter specification."""
    name: str = Field(description="Parameter name")
    type: str = Field(description="Parameter type")
    description: str = Field(description="Parameter description")
    indexed: bool = Field(description="Whether the parameter is indexed", default=False)

class Event(BaseModel):
    """Event specification."""
    name: str = Field(description="Event name")
    description: str = Field(description="Event description")
    parameters: List[EventParameter] = Field(description="Event parameters")

class MethodSpec(BaseModel):
    """Specification for a smart contract method."""
    name: str = Field(description="Method name")
    description: str = Field(description="What the method does")
    params: List[MethodParameter] = Field(description="Input parameters with types")
    returns: MethodReturn = Field(description="Return value specification")
    access_control: List[str] = Field(description="Required roles/permissions")
    state_changes: List[str] = Field(description="State modifications")
    events: List[str] = Field(description="Events to emit")
    validation: List[str] = Field(description="Validation rules")

class RequirementsInput(BaseModel):
    """Input schema for processing contract requirements."""
    description: str = Field(
        description="Detailed description of what the contract should do"
    )
    type: str = Field(
        description="The specific type/purpose of this contract"
    )
    features: List[str] = Field(
        description="List of specific features and functionalities required"
    )
    methods: List[MethodSpec] = Field(
        description="Detailed specifications for contract methods",
        default_factory=list
    )
    state_variables: List[StateVariable] = Field(
        description="State variables and their types",
        default_factory=list
    )
    events: List[Event] = Field(
        description="Events and their parameters",
        default_factory=list
    )

@tool
def ProcessRequirements(requirements: RequirementsInput) -> Dict:
    """Process and structure the user's smart contract requirements."""
    # Extract method specifications
    method_specs = []
    for feature in requirements.features:
        if "method:" in feature.lower() or any(keyword in feature.lower() for keyword in ["create", "update", "delete", "get", "set", "verify", "check", "validate"]):
            # Create basic parameter and return types
            params = [MethodParameter(
                name="input",
                type="string",
                description="Default input parameter"
            )]
            returns = MethodReturn(
                type="void",
                description="Default return type"
            )
            
            method_spec = MethodSpec(
                name=feature.split(":")[0].strip() if ":" in feature else feature.strip(),
                description=feature.split(":")[-1].strip() if ":" in feature else feature.strip(),
                params=params,
                returns=returns,
                access_control=["user"],
                state_changes=[],
                events=[],
                validation=[]
            )
            method_specs.append(method_spec)

    # Extract state variables
    state_vars = []
    state_patterns = ["store", "track", "record", "maintain", "keep", "save"]
    for feature in requirements.features:
        if any(pattern in feature.lower() for pattern in state_patterns):
            state_var = StateVariable(
                name=feature.split(":")[0].strip() if ":" in feature else feature.strip(),
                type="mapping",
                description=feature,
                is_mapping=True
            )
            state_vars.append(state_var)

    # Extract events
    events = []
    event_patterns = ["event", "emit", "notify", "track", "log"]
    for feature in requirements.features:
        if any(pattern in feature.lower() for pattern in event_patterns):
            event_params = [
                EventParameter(
                    name="address",
                    type="Address",
                    description="User address",
                    indexed=True
                ),
                EventParameter(
                    name="timestamp",
                    type="long",
                    description="Event timestamp",
                    indexed=False
                )
            ]
            event = Event(
                name=f"{feature.split(':')[0].strip()}Event" if ":" in feature else f"{feature.strip()}Event",
                description=feature,
                parameters=event_params
            )
            events.append(event)

    return {
        "description": requirements.description,
        "type": requirements.type,
        "features": requirements.features,
        "methods": [method.dict() for method in method_specs],
        "state_variables": [var.dict() for var in state_vars],
        "events": [event.dict() for event in events]
    }

def initialize_state(state: AgentState) -> AgentState:
    """Initialize state with default values if not already present."""
    if "messages" not in state:
        state["messages"] = []
    return state

async def chat_node(state: AgentState, config: RunnableConfig) -> Command[Literal["contract_analyzer", "chat"]]:
    """
    Chat node for gathering and processing user requirements for smart contract generation.
    """
    # Initialize state
    state = initialize_state(state)
    
    # Prepare message history with enhanced context
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content="""Please analyze the smart contract requirements and extract:

1. Core Contract Methods:
   - Method signatures and purposes
   - Input/output specifications
   - Access control rules
   - State changes and events

2. Contract State:
   - Required data structures
   - State variables and types
   - Access patterns

3. Technical Requirements:
   - Platform-specific needs
   - Security considerations
   - Performance requirements

If any specifications are unclear, ask for clarification.""")
    ]
    
    if state["messages"]:
        messages.extend(state["messages"])

    model = get_model(state)
    
    # Get initial response
    response = await model.bind_tools(
        [ProcessRequirements],
    ).ainvoke(messages)

    ai_message = cast(AIMessage, response)
    updated_messages = state["messages"] + [ai_message]
    
    # If no tool calls, ask clarifying questions
    if not ai_message.tool_calls:
        clarification_message = HumanMessage(
            content="""I need more specific details about the smart contract requirements:

1. Contract Methods:
   - What are the main functions needed?
   - What parameters do they take?
   - What should they return?
   - Who can call them?

2. Contract State:
   - What data needs to be stored?
   - What are the data types?
   - How will the data be accessed?

3. Events and Validation:
   - What events should be emitted?
   - What validation rules are needed?
   - What error conditions should be handled?"""
        )
        return Command(
            goto="chat",
            update={"messages": updated_messages + [clarification_message]}
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
            
        # Validate requirements and ensure no empty values
        description = requirements.get("description", "").strip()
        contract_type = requirements.get("type", "").strip()
        features = [f.strip() for f in requirements.get("features", []) if f.strip()]
        methods = requirements.get("methods", [])
        state_variables = requirements.get("state_variables", [])
        events = requirements.get("events", [])
        
        if not description or not contract_type or not features:
            raise ValueError("Missing or empty required fields in requirements")
            
        # Create tool message with detailed feedback
        tool_message = ToolMessage(
            tool_call_id=tool_call["id"],
            content=f"""Requirements processed successfully:

Contract Purpose: {contract_type}
Description: {description}

Core Features:
{chr(10).join(f'- {feature}' for feature in features)}

Methods: {len(methods)} defined
State Variables: {len(state_variables)} defined
Events: {len(events)} defined"""
        )
        
        # Update state with validated fields
        state_update = {
            "messages": updated_messages + [tool_message],
            "user_requirements": description,
            "contract_type": contract_type,
            "contract_features": features,
            "contract_methods": methods,
            "state_variables": state_variables,
            "contract_events": events
        }
        
        return Command(goto="contract_analyzer", update=state_update)
        
    except Exception as e:
        error_message = HumanMessage(
            content=f"""I need more specific information about the contract requirements:

1. Method Specifications:
   - What methods/functions are needed?
   - What are their inputs and outputs?
   - What access controls are required?

2. State Management:
   - What data needs to be stored?
   - What are the data structures?
   - How will state be modified?

3. Events and Security:
   - What events should be tracked?
   - What security measures are needed?
   - What error cases should be handled?

Error: {str(e)}"""
        )
        return Command(
            goto="chat",
            update={"messages": updated_messages + [error_message]}
        ) 
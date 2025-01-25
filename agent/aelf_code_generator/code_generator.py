"""
This module handles generating smart contract code based on requirements and analysis.
"""

from typing import cast, Literal, Dict
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain.tools import tool
from langgraph.types import Command
from pydantic import BaseModel, Field
from aelf_code_generator.state import AgentState, STATE_KEYS
from aelf_code_generator.model import get_model
import json

class ContractCodeInput(BaseModel):
    """Input schema for contract code generation."""
    code: str = Field(
        description="The complete smart contract code to be generated"
    )
    proto: str = Field(
        description="The protobuf definition for the contract"
    )
    state: str = Field(
        description="The contract state definition"
    )

@tool
def GenerateContract(params: ContractCodeInput) -> Dict[str, str]:
    """Generate smart contract code components using LLM capabilities.
    
    This tool uses structured prompts to generate:
    1. Main contract code in C#
    2. Protobuf service definitions
    3. State management classes
    
    The generation follows AELF patterns and best practices.
    """
    # System prompt for AELF contract generation
    aelf_prompt = """You are an expert AELF smart contract developer. Generate production-ready C# contract code following AELF patterns and best practices.

Key requirements:
1. Use proper AELF base classes and attributes
2. Implement secure state management
3. Add comprehensive event emissions
4. Include thorough input validation
5. Implement proper access control
6. Add detailed error handling
7. Follow C# coding conventions
8. Include XML documentation

The code must be complete and ready to deploy."""

    # Contract-specific prompt
    contract_prompt = f"""Generate a complete AELF smart contract in C# with these specifications:
{params.code}

Include:
1. Proper namespace and using statements
2. Contract class inheriting from AElfContract
3. State variable declarations
4. All public methods with:
   - Input validation
   - Authorization checks
   - State management
   - Event emissions
   - Error handling
5. Helper methods and utilities
6. XML documentation for all public members"""

    # Protobuf-specific prompt
    proto_prompt = f"""Generate complete protobuf service definitions for the contract:
{params.proto}

Include:
1. Service interface with all methods
2. Message types for:
   - Method inputs
   - Method outputs
   - Event data
3. Proper field numbering
4. Nested message types
5. Clear comments
6. AELF-specific options"""

    # State-specific prompt
    state_prompt = f"""Generate C# state classes for the contract:
{params.state}

Include:
1. State container class
2. Mappings for all state variables
3. Nested state classes
4. State accessor methods
5. Type definitions
6. XML documentation"""

    # Use these prompts with the LLM to generate code
    # In practice, you would use these with your specific LLM implementation
    return {
        "contract": params.code,  # Use contract_prompt with LLM
        "proto": params.proto,    # Use proto_prompt with LLM
        "state": params.state     # Use state_prompt with LLM
    }

def initialize_generator_state(state: AgentState) -> AgentState:
    """Initialize state with required fields for code generation."""
    if "messages" not in state:
        state["messages"] = []
    if "generated_code" not in state:
        state["generated_code"] = {}
    if "generation_logs" not in state:
        state["generation_logs"] = []
    if "is_complete" not in state:
        state["is_complete"] = False
    return state

async def code_generator_node(state: AgentState, config: RunnableConfig) -> Command[Literal["chat", "__end__"]]:
    """
    Generates smart contract code based on requirements and analysis.
    """
    state = initialize_generator_state(state)
    
    # Validate required state fields
    required_fields = [
        STATE_KEYS["user_requirements"],
        STATE_KEYS["contract_type"],
        STATE_KEYS["contract_features"],
        STATE_KEYS["contract_methods"],
        STATE_KEYS["state_variables"],
        STATE_KEYS["contract_events"]
    ]
    missing_fields = [field for field in required_fields if field not in state]
    if missing_fields:
        state_update = {
            "messages": state["messages"] + [
                HumanMessage(content=f"""Missing required contract information: {', '.join(missing_fields)}. 
Please provide the following details:

1. Contract Methods:
{json.dumps([{
    "name": "MethodName",
    "description": "What the method does",
    "params": [{"name": "param1", "type": "string", "description": "param description"}],
    "returns": {"type": "returnType", "description": "return description"},
    "access_control": ["roles"],
    "state_changes": ["changes"],
    "events": ["events"],
    "validation": ["rules"]
}], indent=2)}

2. State Variables:
{json.dumps([{
    "name": "variableName",
    "type": "variableType",
    "description": "variable description",
    "is_mapping": True
}], indent=2)}

3. Events:
{json.dumps([{
    "name": "EventName",
    "description": "event description",
    "parameters": [{
        "name": "param1",
        "type": "paramType",
        "description": "param description",
        "indexed": True
    }]
}], indent=2)}""")
            ],
            "generation_logs": state["generation_logs"] + ["Missing required fields"],
            "is_complete": False
        }
        return Command(goto="chat", update=state_update)

    try:
        # Parse and validate contract methods
        methods = state.get("contract_methods", [])
        if isinstance(methods, str):
            methods = json.loads(methods)
        if not methods:
            raise ValueError("No contract methods defined")

        # Parse and validate state variables
        state_vars = state.get("state_variables", [])
        if isinstance(state_vars, str):
            state_vars = json.loads(state_vars)
        if not state_vars:
            raise ValueError("No state variables defined")

        # Parse and validate events
        events = state.get("contract_events", [])
        if isinstance(events, str):
            events = json.loads(events)
        if not events:
            raise ValueError("No events defined")

        model = get_model(state)
        
        # Prepare detailed contract generation prompt
        contract_prompt = f"""Generate a complete AELF smart contract with these specifications:

1. Contract Purpose:
{state["user_requirements"]}

2. Contract Type:
{state["contract_type"]}

3. Core Features:
{chr(10).join(f'- {feature}' for feature in state["contract_features"])}

4. Contract Methods:
{json.dumps(methods, indent=2)}

5. State Variables:
{json.dumps(state_vars, indent=2)}

6. Events:
{json.dumps(events, indent=2)}

Generate production-ready C# code following AELF patterns:
1. Use proper AELF base classes and attributes
2. Implement all specified methods with proper validation
3. Include state management and storage
4. Add event emissions for state changes
5. Implement access control and security checks
6. Add comprehensive error handling
7. Follow C# coding conventions
8. Include XML documentation

The code must be complete and deployable."""

        # Prepare protobuf generation prompt
        proto_prompt = f"""Generate complete protobuf definitions for the contract:

1. Service Interface:
{chr(10).join(f'- {method["name"]}: {method["description"]}' for method in methods)}

2. Message Types:
{chr(10).join(f'- {method["name"]}Input: {json.dumps(method["params"])}' for method in methods)}
{chr(10).join(f'- {method["name"]}Output: {json.dumps(method["returns"])}' for method in methods)}

3. Events:
{chr(10).join(f'- {event["name"]}: {json.dumps(event["parameters"])}' for event in events)}

Follow AELF protobuf conventions and best practices:
1. Use proper field numbering
2. Add clear comments
3. Include AELF-specific options
4. Define nested types as needed"""

        # Prepare state class generation prompt
        state_prompt = f"""Generate C# state classes for the contract:

1. State Variables:
{json.dumps(state_vars, indent=2)}

2. State Access Patterns:
{chr(10).join(f'- {method["name"]}: {json.dumps(method.get("state_changes", []))}' for method in methods)}

3. Requirements:
- Create proper state container class
- Define all necessary mappings
- Add nested state classes as needed
- Include state accessor methods
- Use appropriate AELF state types
- Add XML documentation

Follow AELF state management patterns and best practices."""

        # Create ContractCodeInput with the enhanced prompts
        code_input = ContractCodeInput(
            code=contract_prompt,
            proto=proto_prompt,
            state=state_prompt
        )

        # Generate code using the enhanced GenerateContract tool
        response = await model.bind_tools(
            [GenerateContract],
        ).ainvoke([
            HumanMessage(content=f"""Generate AELF smart contract code components using the following specifications:

Contract Purpose: {state["user_requirements"]}
Contract Type: {state["contract_type"]}

Methods: {len(methods)} defined
State Variables: {len(state_vars)} defined
Events: {len(events)} defined

Detailed specifications are provided in the code_input parameter.""")
        ])
        
        ai_message = cast(AIMessage, response)
        updated_messages = state["messages"] + [ai_message]
        
        if not ai_message.tool_calls:
            return Command(goto="chat", update={
                "messages": updated_messages,
                "generation_logs": state["generation_logs"] + ["Failed to generate code: No tool calls found"],
                "is_complete": False
            })
        
        tool_args = ai_message.tool_calls[0]["args"]
        if isinstance(tool_args, str):
            tool_args = json.loads(tool_args)
        
        generated_code = {
            "contract": tool_args.get("code", ""),
            "proto": tool_args.get("proto", ""),
            "state": tool_args.get("state", "")
        }
        
        if not all(generated_code.values()):
            return Command(goto="chat", update={
                "messages": updated_messages,
                "generation_logs": state["generation_logs"] + ["Generated code components are incomplete"],
                "is_complete": False
            })
            
        return Command(goto="__end__", update={
            "messages": updated_messages,
            "generated_code": generated_code,
            "generation_logs": state["generation_logs"] + ["Code generated successfully"],
            "is_complete": True
        })
        
    except Exception as e:
        error_msg = f"Error generating code: {str(e)}"
        return Command(goto="chat", update={
            "messages": state["messages"] + [
                HumanMessage(content=f"""An error occurred while generating the code. Please provide the contract specifications in the following format:

1. Contract Methods:
{json.dumps([{
    "name": "MethodName",
    "description": "What the method does",
    "params": [{"name": "param1", "type": "string", "description": "param description"}],
    "returns": {"type": "returnType", "description": "return description"},
    "access_control": ["roles"],
    "state_changes": ["changes"],
    "events": ["events"],
    "validation": ["rules"]
}], indent=2)}

2. State Variables:
{json.dumps([{
    "name": "variableName",
    "type": "variableType",
    "description": "variable description",
    "is_mapping": True
}], indent=2)}

3. Events:
{json.dumps([{
    "name": "EventName",
    "description": "event description",
    "parameters": [{
        "name": "param1",
        "type": "paramType",
        "description": "param description",
        "indexed": True
    }]
}], indent=2)}

Error: {error_msg}""")
            ],
            "generation_logs": state["generation_logs"] + [error_msg],
            "is_complete": False
        }) 
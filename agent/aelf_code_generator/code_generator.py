"""
This module handles generating smart contract code based on templates and requirements.
"""

from typing import cast, Literal, Dict
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain.tools import tool
from langgraph.types import Command
from pydantic import BaseModel, Field
from copilotkit.langchain import copilotkit_customize_config
from aelf_code_generator.state import AgentState
from aelf_code_generator.model import get_model

class ContractCodeInput(BaseModel):
    """Input schema for contract code generation."""
    code: str = Field(
        description="The complete smart contract code to be generated"
    )

@tool
def GenerateContract(params: ContractCodeInput) -> str:
    """Generate the smart contract code."""
    return params.code

def initialize_generator_state(state: AgentState) -> AgentState:
    """Initialize state with required fields for code generation."""
    if "generated_code" not in state:
        state["generated_code"] = ""
    if "generation_logs" not in state:
        state["generation_logs"] = []
    return state

async def code_generator_node(state: AgentState, config: RunnableConfig) -> Command[Literal["review_code"]]:
    """
    Generates smart contract code based on selected template and requirements.
    """
    # Initialize state
    state = initialize_generator_state(state)
    
    config = copilotkit_customize_config(
        config,
        emit_intermediate_state=[{
            "state_key": "generated_code",
            "tool": "GenerateContract",
            "tool_argument": "params",
        }],
    )

    model = get_model(state)
    
    messages = [
        HumanMessage(
            content=f"""Generate the smart contract code based on:
            1. User Requirements: {state.get('user_requirements', 'Not specified')}
            2. Contract Type: {state.get('contract_type', 'Not specified')}
            3. Requested Features: {', '.join(state.get('contract_features', ['Not specified']))}
            4. Selected Template: {state.get('selected_template', 'Not specified')}
            5. GitHub Analysis: {state.get('github_analysis', 'Not available')}
            
            Follow AELF smart contract best practices and patterns.
            Include all necessary imports and dependencies.
            Ensure the contract is secure and efficient.
            
            If there are any improvement suggestions from previous iterations, address them:
            {state.get('improvement_feedback', 'No previous feedback')}
            """
        )
    ]

    response = await model.bind_tools(
        [GenerateContract],
    ).ainvoke(messages, config)

    ai_message = cast(AIMessage, response)
    
    if not ai_message.tool_calls:
        # If no code was generated, log the error and continue
        state["generation_logs"].append("Failed to generate code: No tool calls found")
        return Command(goto="review_code", update=state)
    
    # Update state with generated code
    tool_args = ai_message.tool_calls[0]["args"]
    if isinstance(tool_args, str):
        import json
        tool_args = json.loads(tool_args)
    
    state["generated_code"] = tool_args.get("code", "")
    state["messages"].append(ai_message)
    
    return Command(goto="review_code", update=state) 
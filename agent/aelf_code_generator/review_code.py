"""
This module handles reviewing and improving generated smart contract code.
"""

from typing import cast, Literal, Dict, List
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain.tools import tool
from langgraph.types import Command
from pydantic import BaseModel, Field
from copilotkit.langchain import copilotkit_customize_config
from aelf_code_generator.state import AgentState
from aelf_code_generator.model import get_model

class CodeReviewInput(BaseModel):
    """Input schema for code review feedback."""
    improvements: List[str] = Field(
        description="List of suggested code improvements"
    )
    security_issues: List[str] = Field(
        description="List of identified security issues"
    )
    gas_optimizations: List[str] = Field(
        description="List of suggested gas optimizations"
    )
    missing_features: List[str] = Field(
        description="List of features that are missing or incomplete"
    )
    suggestions: List[str] = Field(
        description="General suggestions for improvement"
    )

@tool
def ReviewCode(feedback: CodeReviewInput) -> Dict:
    """Process code review feedback and suggest improvements."""
    return feedback.dict()

def initialize_review_state(state: AgentState) -> AgentState:
    """Initialize state with required fields for code review."""
    if "review_feedback" not in state:
        state["review_feedback"] = {}
    if "improvement_feedback" not in state:
        state["improvement_feedback"] = {}
    if "is_complete" not in state:
        state["is_complete"] = False
    return state

async def review_code_node(state: AgentState, config: RunnableConfig) -> Command[Literal["code_generator", "chat", "__end__"]]:
    """
    Reviews generated code and processes feedback.
    """
    # Initialize state
    state = initialize_review_state(state)
    
    config = copilotkit_customize_config(
        config,
        emit_intermediate_state=[{
            "state_key": "review_feedback",
            "tool": "ReviewCode",
            "tool_argument": "feedback",
        }],
    )

    model = get_model(state)
    
    messages = [
        HumanMessage(
            content=f"""Review the generated smart contract code and provide feedback:
            
            Generated Code:
            {state.get('generated_code', 'No code generated')}
            
            Original Requirements:
            - Type: {state.get('contract_type', 'Not specified')}
            - Features: {', '.join(state.get('contract_features', ['Not specified']))}
            
            Consider:
            1. Code quality and best practices
            2. Security considerations
            3. Gas efficiency
            4. Feature completeness
            
            Previous feedback (if any):
            {state.get('improvement_feedback', 'No previous feedback')}
            
            Use the ReviewCode tool to provide structured feedback.
            If the code meets all requirements and no improvements are needed, indicate completion.
            """
        )
    ]

    response = await model.bind_tools(
        [ReviewCode],
    ).ainvoke(messages, config)

    ai_message = cast(AIMessage, response)
    
    # Process the review feedback
    if ai_message.tool_calls:
        tool_args = ai_message.tool_calls[0]["args"]
        if isinstance(tool_args, str):
            import json
            tool_args = json.loads(tool_args)
            
        feedback = tool_args.get("feedback", {})
        state["review_feedback"] = feedback
        
        # If there are improvements needed
        if any(feedback.values()):
            state["improvement_feedback"] = feedback
            state["messages"].append(ai_message)
            return Command(goto="code_generator", update=state)
            
    # Check if we need to modify requirements
    if any(phrase in ai_message.content.lower() for phrase in ["modify requirements", "change requirements", "update requirements"]):
        state["messages"].append(HumanMessage(
            content="The current requirements need to be updated. Could you please provide more specific details about what needs to be changed?"
        ))
        return Command(goto="chat", update=state)
    
    # If no improvements needed and requirements are met
    state["is_complete"] = True
    state["messages"].append(ai_message)
    return Command(goto="__end__", update=state) 
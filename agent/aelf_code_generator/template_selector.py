"""
This module handles selecting appropriate templates for smart contract generation.
"""

from typing import cast, Literal
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from aelf_code_generator.state import AgentState
from aelf_code_generator.model import get_model

def initialize_template_state(state: AgentState) -> AgentState:
    """Initialize state with required fields for template selection."""
    if "selected_template" not in state:
        state["selected_template"] = ""
    if "template_analysis" not in state:
        state["template_analysis"] = ""
    return state

async def template_selector_node(state: AgentState, config: RunnableConfig) -> Command[Literal["code_generator", "chat"]]:
    """
    Selects appropriate template based on requirements and analysis.
    """
    # Initialize state
    state = initialize_template_state(state)
    
    model = get_model(state)
    
    messages = [
        HumanMessage(
            content=f"""Based on the analyzed GitHub resources and user requirements, select the most appropriate template.
            
            User Requirements: {state.get('user_requirements', 'Not specified')}
            Contract Type: {state.get('contract_type', 'Not specified')}
            Requested Features: {', '.join(state.get('contract_features', ['Not specified']))}
            GitHub Analysis: {state.get('github_analysis', 'Not available')}
            
            Focus on AELF contract patterns and best practices.
            Consider the specific requirements and features requested by the user.
            If the requirements don't match any template well, we should ask for clarification.
            """
        )
    ]

    response = await model.ainvoke(messages, config)
    ai_message = cast(AIMessage, response)
    
    # Update state with template analysis
    state["template_analysis"] = ai_message.content
    
    # If no suitable template found or clarification needed, go back to chat
    if any(phrase in ai_message.content.lower() for phrase in ["need clarification", "unclear", "more information needed"]):
        state["messages"].append(HumanMessage(
            content="I need more specific information about your requirements to select an appropriate template. Could you please provide more details?"
        ))
        return Command(goto="chat", update=state)
    
    # Extract selected template from analysis
    state["selected_template"] = ai_message.content
    
    return Command(goto="code_generator", update=state) 
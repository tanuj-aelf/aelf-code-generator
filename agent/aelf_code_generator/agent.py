"""
This module defines the main agent workflow for AELF smart contract code generation.
"""

from typing import Dict, List, Any, Annotated
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.graph.message import add_messages
from aelf_code_generator.model import get_model
from aelf_code_generator.types import AgentState, get_default_state

SYSTEM_PROMPT = """You are an expert AELF smart contract developer. Your task is to analyze the dApp description and generate a complete smart contract implementation.

Follow these steps in order:
1. Analyze the requirements and identify:
   - Contract type and purpose
   - Core features and functionality
   - Required methods and their specifications
   - State variables and storage needs
   - Events and their parameters
   - Access control and security requirements

2. Generate complete, production-ready code including:
   - Main contract class in C# with proper AELF base classes
   - State management classes with proper mappings
   - Protobuf service and message definitions
   - Event declarations and emissions
   - Access control implementation
   - Input validation and error handling
   - XML documentation

Make reasonable assumptions for any missing details based on common blockchain patterns.
Format the code output in clear code blocks:
- C# contract code in ```csharp blocks
- State classes in ```csharp blocks
- Protobuf definitions in ```protobuf blocks

Ensure the code follows AELF best practices and is ready for deployment."""

async def process_contract(state: AgentState) -> AgentState:
    """Process the dApp description and generate smart contract code."""
    try:
        # Get model with state
        model = get_model(state)
        
        # Generate complete analysis and code
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=state["input"])
        ]
        
        response = await model.ainvoke(messages)
        content = response.content
        
        # Extract analysis (everything before first code block)
        analysis = content.split("```")[0].strip()
        
        # Parse code blocks
        components = {
            "contract": "",
            "state": "",
            "proto": ""
        }
        
        current_component = None
        for line in content.split("\n"):
            if "```csharp" in line or "```c#" in line:
                current_component = "contract" if "contract" not in components["contract"] else "state"
            elif "```protobuf" in line:
                current_component = "proto"
            elif "```" in line:
                current_component = None
            elif current_component:
                components[current_component] += line + "\n"
        
        # Update state with results
        state["output"] = {
            "contract": components["contract"].strip(),
            "state": components["state"].strip(),
            "proto": components["proto"].strip(),
            "analysis": analysis
        }
        
        return state
        
    except Exception as e:
        # In case of error, return empty results with error message
        state["output"] = {
            "contract": "",
            "state": "",
            "proto": "",
            "analysis": f"Error generating contract: {str(e)}"
        }
        return state

def create_agent():
    """Create the agent workflow."""
    workflow = StateGraph(AgentState)
    
    # Add single processing node
    workflow.add_node("process", process_contract)
    
    # Set entry point and connect to end
    workflow.set_entry_point("process")
    workflow.add_edge("process", END)
    
    # Compile workflow
    return workflow.compile()

# Create the graph
graph = create_agent()

# Export
__all__ = ["graph"] 
"""
This module defines the main agent workflow for AELF smart contract code generation.
"""

from typing import Dict, List, Any, Annotated, Literal
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.graph.message import add_messages
from langgraph.types import Command
from aelf_code_generator.model import get_model
from aelf_code_generator.types import AgentState, ContractOutput, get_default_state

ANALYSIS_PROMPT = """You are an expert AELF smart contract developer. Your task is to analyze the dApp description and provide a detailed analysis.

Analyze the requirements and identify:
- Contract type and purpose
- Core features and functionality
- Required methods and their specifications
- State variables and storage needs
- Events and their parameters
- Access control and security requirements

Provide a structured analysis that will be used to generate the smart contract code in the next step.
Do not generate any code in this step, focus only on the analysis."""

CODE_GENERATION_PROMPT = """You are an expert AELF smart contract developer. Based on the provided analysis, generate a complete smart contract implementation.

Generate complete, production-ready code including:
- Main contract class in C# with proper AELF base classes
- State management classes with proper mappings
- Protobuf service and message definitions
- Event declarations and emissions
- Access control implementation
- Input validation and error handling
- XML documentation

Format the code output in clear code blocks:
- C# contract code in ```csharp blocks
- State classes in ```csharp blocks
- Protobuf definitions in ```protobuf blocks

Ensure the code follows AELF best practices and is ready for deployment."""

async def analyze_requirements(state: AgentState) -> Command[Literal["generate", "__end__"]]:
    """Analyze the dApp description and provide detailed requirements analysis."""
    try:
        # Get model with state
        model = get_model(state)
        
        # Generate analysis
        messages = [
            SystemMessage(content=ANALYSIS_PROMPT),
            HumanMessage(content=state["input"])
        ]
        
        response = await model.ainvoke(messages)
        analysis = response.content.strip()
        
        if not analysis:
            raise ValueError("Analysis generation failed - empty response")
            
        # Return command to move to next state
        return Command(
            goto="generate",
            update={
                "output": {
                    "contract": "",
                    "state": "",
                    "proto": "",
                    "analysis": analysis
                }
            }
        )
        
    except Exception as e:
        error_msg = f"Error analyzing requirements: {str(e)}"
        return Command(
            goto="__end__",
            update={
                "output": {
                    "contract": "",
                    "state": "",
                    "proto": "",
                    "analysis": error_msg
                }
            }
        )

async def generate_contract(state: AgentState) -> Command[Literal["__end__"]]:
    """Generate smart contract code based on the analysis."""
    try:
        # Get analysis from previous state
        analysis = state["output"]["analysis"]
        if not analysis:
            raise ValueError("No analysis available for code generation")
            
        # Get model with state
        model = get_model(state)
        
        # Generate code based on analysis
        messages = [
            SystemMessage(content=CODE_GENERATION_PROMPT),
            HumanMessage(content=f"Analysis:\n{analysis}\n\nPlease generate the complete smart contract code based on this analysis.")
        ]
        
        response = await model.ainvoke(messages)
        content = response.content
        
        if not content:
            raise ValueError("Code generation failed - empty response")
            
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
            elif current_component and current_component in components:
                components[current_component] += line + "\n"
        
        # Ensure all components have at least empty string values
        components = {k: v.strip() or "" for k, v in components.items()}
        
        # Return command with results
        return Command(
            goto="__end__",
            update={
                "output": {
                    "contract": components["contract"],
                    "state": components["state"],
                    "proto": components["proto"],
                    "analysis": analysis
                }
            }
        )
        
    except Exception as e:
        error_msg = f"Error generating contract: {str(e)}"
        return Command(
            goto="__end__",
            update={
                "output": {
                    "contract": "",
                    "state": "",
                    "proto": "",
                    "analysis": error_msg
                }
            }
        )

def create_agent():
    """Create the agent workflow."""
    workflow = StateGraph(AgentState)
    
    # Add analysis and code generation nodes
    workflow.add_node("analyze", analyze_requirements)
    workflow.add_node("generate", generate_contract)
    
    # Set entry point and connect nodes
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "generate")
    workflow.add_edge("analyze", END)  # In case of analysis error
    workflow.add_edge("generate", END)
    
    # Compile workflow
    return workflow.compile()

# Create the graph
graph = create_agent()

# Export
__all__ = ["graph", "get_default_state"] 
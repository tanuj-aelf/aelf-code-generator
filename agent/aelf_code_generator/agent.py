"""
This module defines the main agent workflow for AELF smart contract code generation.
"""

import os
from typing import Dict, List, Any, Annotated, Literal
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.graph.message import add_messages
from langgraph.types import Command
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from aelf_code_generator.model import get_model
from aelf_code_generator.types import AgentState, ContractOutput, CodebaseInsight, get_default_state

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

CODEBASE_ANALYSIS_PROMPT = """You are an expert AELF smart contract developer. Based on the provided analysis and sample codebase insights, analyze and extract best practices and patterns.

Focus on:
1. Project structure and organization
2. Common coding patterns in AELF smart contracts
3. Implementation guidelines specific to the requirements
4. Relevant sample contracts that can be used as reference

Provide structured insights that will guide the code generation process."""

CODE_GENERATION_PROMPT = """You are an expert AELF smart contract developer. Based on the provided analysis and codebase insights, generate a complete smart contract implementation.

Follow these implementation guidelines:
{implementation_guidelines}

Common coding patterns to use:
{coding_patterns}

Project structure to follow:
{project_structure}

Relevant sample references:
{relevant_samples}

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

async def analyze_requirements(state: AgentState) -> Command[Literal["analyze_codebase", "__end__"]]:
    """Analyze the dApp description and provide detailed requirements analysis."""
    try:
        # Initialize internal state if not present
        if "_internal" not in state:
            state["_internal"] = {
                "analysis": "",
                "codebase_insights": {
                    "project_structure": "",
                    "coding_patterns": "",
                    "relevant_samples": [],
                    "implementation_guidelines": ""
                },
                "output": {
                    "contract": "",
                    "state": "",
                    "proto": "",
                    "analysis": ""
                }
            }
            
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
            goto="analyze_codebase",
            update={
                "_internal": {
                    "analysis": analysis,
                    "codebase_insights": state["_internal"]["codebase_insights"],
                    "output": {
                        "contract": "",
                        "state": "",
                        "proto": "",
                        "analysis": analysis
                    }
                }
            }
        )
        
    except Exception as e:
        error_msg = f"Error analyzing requirements: {str(e)}"
        return Command(
            goto="__end__",
            update={
                "_internal": {
                    "analysis": error_msg,
                    "codebase_insights": {
                        "project_structure": "",
                        "coding_patterns": "",
                        "relevant_samples": [],
                        "implementation_guidelines": ""
                    },
                    "output": {
                        "contract": "",
                        "state": "",
                        "proto": "",
                        "analysis": error_msg
                    }
                }
            }
        )

async def analyze_codebase(state: AgentState) -> Command[Literal["generate", "__end__"]]:
    """Analyze AELF sample codebases to gather implementation insights."""
    try:
        # Initialize Tavily search with API key
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not tavily_api_key:
            raise ValueError("TAVILY_API_KEY not found in environment variables")
            
        search = TavilySearchAPIWrapper(tavily_api_key=tavily_api_key)
        
        # Prepare search queries based on analysis
        analysis = state["_internal"]["analysis"]
        
        # First try to determine the type of contract from analysis
        contract_type = "smart contract"  # default
        if "NFT" in analysis or "token" in analysis.lower():
            contract_type = "NFT contract"
        elif "DAO" in analysis.lower():
            contract_type = "DAO contract"
        elif "game" in analysis.lower():
            contract_type = "game contract"
            
        # Prepare focused queries
        queries = [
            f"site:github.com/AElfProject/aelf-samples {contract_type} implementation example",
            f"site:github.com/AElfProject/aelf-samples {contract_type} structure patterns",
            "site:github.com/AElfProject/aelf-samples contract state management protobuf example"
        ]
        
        # Gather insights from sample codebases
        all_results = []
        for query in queries:
            try:
                results = search.results(query, search_depth="advanced", max_results=5)
                all_results.extend(results)
            except Exception as e:
                print(f"Search error for query '{query}': {str(e)}")
                continue
        
        if not all_results:
            # Fallback to model-based insights if search fails
            insights_dict = {
                "project_structure": """Standard AELF project structure:
1. Contract class inheriting from AElfContract
2. State class for data storage
3. Proto files for interface definition""",
                "coding_patterns": """Common AELF patterns:
1. State management using MapState/SingletonState
2. Event emission for status changes
3. Authorization checks using Context.Sender""",
                "relevant_samples": ["https://github.com/AElfProject/aelf-samples"],
                "implementation_guidelines": """Follow AELF best practices:
1. Use proper base classes
2. Implement state management
3. Add proper access control
4. Include input validation
5. Emit events for state changes"""
            }
        else:
            # Get model to analyze search results
            model = get_model(state)
            
            # Generate codebase insights
            messages = [
                SystemMessage(content=CODEBASE_ANALYSIS_PROMPT),
                HumanMessage(content=f"""
Analysis: {analysis}

Search Results:
{all_results}

Please analyze these results and provide structured insights for code generation.
""")
            ]
            
            response = await model.ainvoke(messages)
            insights = response.content.strip()
            
            if not insights:
                raise ValueError("Codebase analysis failed - empty response")
                
            # Parse insights into structured format
            insights_dict = {
                "project_structure": "Standard AELF project structure with contract, state, and proto files",
                "coding_patterns": insights.split("Common coding patterns:")[1].split("\n")[0] if "Common coding patterns:" in insights else "",
                "relevant_samples": [r["url"] for r in all_results if "github.com" in r["url"]],
                "implementation_guidelines": insights
            }
        
        # Return command to move to next state
        return Command(
            goto="generate",
            update={
                "_internal": {
                    **state["_internal"],
                    "codebase_insights": insights_dict
                }
            }
        )
        
    except Exception as e:
        error_msg = f"Error analyzing codebase: {str(e)}"
        print(f"Codebase analysis error: {error_msg}")  # Add logging
        return Command(
            goto="generate",  # Continue to generate even if codebase analysis fails
            update={
                "_internal": {
                    **state["_internal"],
                    "codebase_insights": {
                        "project_structure": """Standard AELF project structure:
1. Contract class inheriting from AElfContract
2. State class for data storage
3. Proto files for interface definition""",
                        "coding_patterns": """Common AELF patterns:
1. State management using MapState/SingletonState
2. Event emission for status changes
3. Authorization checks using Context.Sender""",
                        "relevant_samples": ["https://github.com/AElfProject/aelf-samples"],
                        "implementation_guidelines": """Follow AELF best practices:
1. Use proper base classes
2. Implement state management
3. Add proper access control
4. Include input validation
5. Emit events for state changes"""
                    }
                }
            }
        )

async def generate_contract(state: AgentState) -> Command[Literal["__end__"]]:
    """Generate smart contract code based on analysis and codebase insights."""
    try:
        # Get analysis and insights
        internal = state["_internal"]
        analysis = internal["analysis"]
        insights = internal["codebase_insights"]
        
        if not analysis or not insights["implementation_guidelines"]:
            raise ValueError("Missing analysis or codebase insights")
            
        # Get model with state
        model = get_model(state)
        
        # Generate code based on analysis and insights
        messages = [
            SystemMessage(content=CODE_GENERATION_PROMPT.format(
                implementation_guidelines=insights["implementation_guidelines"],
                coding_patterns=insights["coding_patterns"],
                project_structure=insights["project_structure"],
                relevant_samples="\n".join(insights["relevant_samples"])
            )),
            HumanMessage(content=f"Analysis:\n{analysis}\n\nPlease generate the complete smart contract code based on this analysis and insights.")
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
                "_internal": {
                    **state["_internal"],
                    "output": {
                        "contract": components["contract"],
                        "state": components["state"],
                        "proto": components["proto"],
                        "analysis": analysis
                    }
                }
            }
        )
        
    except Exception as e:
        error_msg = f"Error generating contract: {str(e)}"
        return Command(
            goto="__end__",
            update={
                "_internal": {
                    **state["_internal"],
                    "output": {
                        "contract": "",
                        "state": "",
                        "proto": "",
                        "analysis": error_msg
                    }
                }
            }
        )

def create_agent():
    """Create the agent workflow."""
    workflow = StateGraph(AgentState)
    
    # Add nodes for each step
    workflow.add_node("analyze", analyze_requirements)
    workflow.add_node("analyze_codebase", analyze_codebase)
    workflow.add_node("generate", generate_contract)
    
    # Set entry point and connect nodes
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "analyze_codebase")
    workflow.add_edge("analyze", END)  # In case of analysis error
    workflow.add_edge("analyze_codebase", "generate")
    workflow.add_edge("analyze_codebase", END)  # In case of codebase analysis error
    workflow.add_edge("generate", END)
    
    # Compile workflow
    return workflow.compile()

# Create the graph
graph = create_agent()

# Export
__all__ = ["graph", "get_default_state"] 
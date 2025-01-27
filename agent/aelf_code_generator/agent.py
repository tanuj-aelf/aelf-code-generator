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

CODE_GENERATION_PROMPT = """You are an expert AELF smart contract developer. Based on the provided analysis and codebase insights, generate a complete smart contract implementation following AELF's standard project structure.

Follow these implementation guidelines:
{implementation_guidelines}

Common coding patterns to use:
{coding_patterns}

Project structure to follow:
{project_structure}

Relevant sample references:
{relevant_samples}

Generate the following files with proper implementations:

1. Main Contract File (src/ContractName.cs):
- Inherit from ContractNameContainer.ContractNameBase
- Implement all contract methods
- Use proper state management
- Include XML documentation
- Add proper access control
- Include input validation
- Emit events for state changes

2. State Class File (src/ContractState.cs):
- Define all state variables using proper AELF state types
- Use MappedState for collections
- Use SingletonState for single values
- Include XML documentation

3. Proto File (src/Protobuf/contract/contract_name.proto):
- Define all messages and services
- Use proper protobuf types
- Include method definitions
- Define events
- Add proper comments

4. Reference Contract File (src/ContractReference.cs):
- Define contract reference state
- Include necessary contract references
- Add helper methods

5. Project File (ContractName.csproj):
- Include necessary AELF package references
- Set proper SDK version
- Configure protobuf generation

Format each file in a separate code block with proper file path comment:
```csharp
// src/ContractName.cs
... contract implementation ...
```

```csharp
// src/ContractState.cs
... state class implementation ...
```

```protobuf
// src/Protobuf/contract/contract_name.proto
... proto definitions ...
```

```csharp
// src/ContractReference.cs
... contract references ...
```

```xml
// ContractName.csproj
... project configuration ...
```

Ensure all files follow AELF conventions and best practices."""

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
            HumanMessage(content=f"Analysis:\n{analysis}\n\nPlease generate the complete smart contract implementation following AELF's project structure.")
        ]
        
        try:
            # Set a longer timeout for code generation
            response = await model.ainvoke(messages, timeout=150)  # 5 minutes timeout
            content = response.content
            
            if not content:
                raise ValueError("Code generation failed - empty response")
        except TimeoutError:
            print("Code generation timed out, using partial response if available")
            content = getattr(response, 'content', '') or ""
            if not content:
                raise ValueError("Code generation timed out and no partial response available")
        
        # Initialize components with empty strings
        components = {
            "contract": "",
            "state": "",
            "proto": "",
            "reference": "",
            "project": ""
        }
        
        # Parse code blocks
        current_component = None
        current_content = []
        in_code_block = False
        
        for line in content.split("\n"):
            # Handle code block markers
            if "```" in line:
                if in_code_block:
                    # End of code block
                    if current_component and current_content:
                        components[current_component] = "\n".join(current_content).strip()
                    current_content = []
                    current_component = None
                in_code_block = not in_code_block
                continue
            
            # Handle file path markers
            if "// src/" in line or "// " in line:
                if "ContractName.cs" in line or "TaskContract.cs" in line:
                    current_component = "contract"
                elif "ContractState.cs" in line or "State.cs" in line:
                    current_component = "state"
                elif ".proto" in line:
                    current_component = "proto"
                elif "ContractReference.cs" in line or "Reference.cs" in line:
                    current_component = "reference"
                elif ".csproj" in line:
                    current_component = "project"
                continue
            
            # Collect content if in a code block and have a current component
            if in_code_block and current_component:
                current_content.append(line)
        
        # Add last component if any
        if current_component and current_content:
            components[current_component] = "\n".join(current_content).strip()
        
        # Ensure all components have content
        if not any(components.values()):
            raise ValueError("No code components were successfully parsed")
        
        # Log the components for debugging
        print("Generated components:")
        for key, value in components.items():
            print(f"{key}: {len(value)} characters")
        
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
                        "reference": components.get("reference", ""),
                        "project": components.get("project", ""),
                        "analysis": analysis
                    }
                }
            }
        )
        
    except Exception as e:
        error_msg = f"Error generating contract: {str(e)}"
        print(f"Generation error: {error_msg}")  # Add logging
        return Command(
            goto="__end__",
            update={
                "_internal": {
                    **state["_internal"],
                    "output": {
                        "contract": "",
                        "state": "",
                        "proto": "",
                        "reference": "",
                        "project": "",
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
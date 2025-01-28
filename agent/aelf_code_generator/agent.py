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
        # First try to determine the type of contract from analysis
        analysis = state["_internal"]["analysis"]
        contract_type = "smart contract"  # default
        
        # Identify relevant sample based on contract type
        relevant_samples = []
        if "NFT" in analysis or "token" in analysis.lower():
            contract_type = "NFT contract"
            relevant_samples = ["nft"]
        elif "DAO" in analysis.lower():
            contract_type = "DAO contract"
            relevant_samples = ["simple-dao"]
        elif "game" in analysis.lower():
            contract_type = "game contract"
            relevant_samples = ["lottery-game", "tic-tac-toe"]
        elif "todo" in analysis.lower():
            contract_type = "todo contract"
            relevant_samples = ["todo"]
        elif "vote" in analysis.lower():
            contract_type = "voting contract"
            relevant_samples = ["vote"]
        elif "allowance" in analysis.lower() or "spending" in analysis.lower():
            contract_type = "allowance contract"
            relevant_samples = ["allowance"]
        elif "staking" in analysis.lower():
            contract_type = "staking contract"
            relevant_samples = ["staking"]
        elif "donation" in analysis.lower():
            contract_type = "donation contract"
            relevant_samples = ["donation"]
        elif "expense" in analysis.lower() or "tracking" in analysis.lower():
            contract_type = "expense tracking contract"
            relevant_samples = ["expense-tracker"]
        else:
            # For basic contracts, look at hello-world
            relevant_samples = ["hello-world"]
            
        # Get model to analyze requirements
        model = get_model(state)
        
        # Generate codebase insights with improved prompt
        messages = [
            SystemMessage(content="""You are an expert AELF smart contract developer. Based on the contract requirements and AELF sample contracts, provide implementation insights and patterns.
Focus on practical, concrete patterns that can be directly applied to smart contract development.
For each pattern you identify, include a brief explanation of why it's important and how it should be used.

Your response should be structured in these sections:
1. Project Structure - How the contract files should be organized
2. Coding Patterns - Common patterns and practices to use
3. Implementation Guidelines - Specific guidance for this contract type
4. Relevant Samples - Which sample contracts to reference

Be specific and detailed in your guidance."""),
            HumanMessage(content=f"""
Based on the following contract requirements and type, provide implementation insights and patterns from AELF sample contracts.

Contract Requirements:
{analysis}

Contract Type: {contract_type}
Relevant Sample(s): {', '.join(relevant_samples)}

Please provide structured insights focusing on:

1. Project Structure and Organization
   - Required contract files and their purpose
   - State variables and their types
   - Events and their parameters
   - Contract references needed

2. Smart Contract Patterns
   - State management patterns for this type
   - Access control patterns needed
   - Event handling patterns
   - Common utility functions
   - Error handling strategies

3. Implementation Guidelines
   - Best practices for this contract type
   - Security considerations
   - Performance optimizations
   - Testing approaches

4. Code Examples
   - Key methods to implement
   - Common features needed
   - Pitfalls to avoid

Your insights will guide the code generation process.""")
        ]
        
        try:
            response = await model.ainvoke(messages, timeout=150)
            insights = response.content.strip()
            
            if not insights:
                raise ValueError("Codebase analysis failed - empty response")
                
            # Split insights into sections
            sections = insights.split("\n\n")
            
            # Extract sections based on headers
            project_structure = ""
            coding_patterns = ""
            implementation_guidelines = insights  # Keep full response as guidelines
            
            for i, section in enumerate(sections):
                section_lower = section.lower()
                if any(header in section_lower for header in ["project structure", "file structure", "organization"]):
                    project_structure = section
                    # Look ahead for subsections
                    for next_section in sections[i+1:]:
                        if not any(header in next_section.lower() for header in ["pattern", "guideline", "implementation"]):
                            project_structure += "\n\n" + next_section
                        else:
                            break
                elif any(header in section_lower for header in ["pattern", "practice", "common"]):
                    coding_patterns = section
                    # Look ahead for subsections
                    for next_section in sections[i+1:]:
                        if not any(header in next_section.lower() for header in ["guideline", "implementation", "structure"]):
                            coding_patterns += "\n\n" + next_section
                        else:
                            break
            
            # Ensure we have content for each section
            if not project_structure:
                project_structure = """Standard AELF project structure:
1. Main Contract Implementation (ContractName.cs)
   - Inherits from ContractBase
   - Contains contract logic
   - Uses state management
   - Includes documentation

2. Contract State (ContractState.cs)
   - Defines state variables
   - Uses proper AELF types
   - Includes documentation

3. Protobuf Definitions (Protobuf/)
   - contract/ - Interface
   - message/ - Messages
   - reference/ - References

4. Contract References (ContractReferences.cs)
   - Reference declarations
   - Helper methods"""

            if not coding_patterns:
                coding_patterns = """Common AELF patterns:
1. State Management
   - MapState for collections
   - SingletonState for values
   - State initialization
   - Access patterns

2. Access Control
   - Context.Sender checks
   - Ownership patterns
   - Authorization
   - Least privilege

3. Event Handling
   - Event definitions
   - State change events
   - Event parameters
   - Documentation

4. Input Validation
   - Parameter validation
   - State validation
   - Error messages
   - Fail-fast approach

5. Error Handling
   - Exception types
   - Error messages
   - Edge cases
   - AELF patterns"""
                
            # Create insights dictionary with extracted sections
            insights_dict = {
                "project_structure": project_structure,
                "coding_patterns": coding_patterns,
                "relevant_samples": relevant_samples,
                "implementation_guidelines": implementation_guidelines
            }
                
        except Exception as e:
            print(f"Error analyzing requirements: {str(e)}")
            raise
            
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
        print(f"Codebase analysis error: {error_msg}")
        return Command(
            goto="generate",  # Continue to generate even if codebase analysis fails
            update={
                "_internal": {
                    **state["_internal"],
                    "codebase_insights": {
                        "project_structure": """Standard AELF project structure:
1. Contract class inheriting from AElfContract
2. State class for data storage
3. Proto files for interface definition
4. Project configuration in .csproj""",
                        "coding_patterns": """Common AELF patterns:
1. State management using MapState/SingletonState
2. Event emission for status changes
3. Authorization checks using Context.Sender
4. Input validation with proper error handling""",
                        "relevant_samples": ["hello-world"],
                        "implementation_guidelines": """Follow AELF best practices:
1. Use proper base classes and inheritance
2. Implement robust state management
3. Add proper access control checks
4. Include comprehensive input validation
5. Emit events for important state changes
6. Follow proper error handling patterns
7. Add XML documentation for all public members"""
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
                
        # Initialize components with empty CodeFile structures
        empty_code_file = {"content": "", "file_type": "", "path": ""}
        components = {
            "contract": dict(empty_code_file),
            "state": dict(empty_code_file),
            "proto": dict(empty_code_file),
            "reference": dict(empty_code_file),
            "project": dict(empty_code_file)
        }
        additional_files = []  # List to store additional files
        
        # Parse code blocks
        current_component = None
        current_content = []
        in_code_block = False
        current_file_type = ""
        
        # Track if we're inside XML documentation
        in_xml_doc = False
        xml_doc_content = []
        
        for line in content.split("\n"):
            # Handle XML documentation
            if "///" in line or "/<" in line:
                in_xml_doc = True
                xml_doc_content.append(line)
                continue
            elif in_xml_doc and (">" in line or line.strip().endswith("/")):
                in_xml_doc = False
                xml_doc_content.append(line)
                if current_content:
                    current_content.extend(xml_doc_content)
                xml_doc_content = []
                continue
            elif in_xml_doc:
                xml_doc_content.append(line)
                continue
                
            # Handle code block markers
            if "```" in line:
                if not in_code_block:
                    # Start of code block - detect language
                    if "csharp" in line.lower():
                        current_file_type = "csharp"
                    elif "protobuf" in line.lower() or "proto" in line.lower():
                        current_file_type = "proto"
                    elif "xml" in line.lower():
                        current_file_type = "xml"
                    else:
                        current_file_type = "text"
                else:
                    # End of code block
                    if current_component and current_content:
                        code_content = "\n".join(current_content).strip()
                        if current_component in components:
                            components[current_component]["content"] = code_content
                            components[current_component]["file_type"] = current_file_type
                        else:
                            # Only store non-empty additional files
                            if code_content and current_file_type:
                                additional_files.append({
                                    "content": code_content,
                                    "file_type": current_file_type,
                                    "path": components.get(current_component, {}).get("path", "")
                                })
                    current_content = []
                    current_component = None
                    current_file_type = ""
                in_code_block = not in_code_block
                continue
            
            # Handle file path markers
            if ("// src/" in line or "// " in line or "<!-- " in line):
                # Skip if it's just a comment about the file path in code
                if in_code_block and not line.strip().startswith("//") and not line.strip().startswith("<!--"):
                    current_content.append(line)
                    continue
                    
                file_path = (
                    line.replace("// ", "")
                    .replace("<!-- ", "")
                    .replace(" -->", "")
                    .strip()
                )
                
                # First check for project file since it has a different comment style
                if ".csproj" in line:
                    current_component = "project"
                    components[current_component]["path"] = file_path
                    components[current_component]["file_type"] = "xml"
                # Then check for other files
                elif "TaskContract.cs" in line or "Contract.cs" in line:
                    current_component = "contract"
                    components[current_component]["path"] = file_path
                    components[current_component]["file_type"] = "csharp"
                elif "ContractState.cs" in line or "State.cs" in line:
                    current_component = "state"
                    components[current_component]["path"] = file_path
                    components[current_component]["file_type"] = "csharp"
                elif ".proto" in line:
                    current_component = "proto"
                    components[current_component]["path"] = file_path
                    components[current_component]["file_type"] = "proto"
                elif "ContractReference.cs" in line or "Reference.cs" in line:
                    current_component = "reference"
                    components[current_component]["path"] = file_path
                    components[current_component]["file_type"] = "csharp"
                else:
                    # Only create additional file entry if it's a real file path
                    if "." in file_path and "/" in file_path:
                        current_component = "additional"
                        additional_files.append({
                            "content": "",  # Will be filled when code block ends
                            "file_type": "",  # Will be set when code block starts
                            "path": file_path
                        })
                continue
            
            # Collect content if in a code block and have a current component
            if in_code_block and current_component:
                current_content.append(line)
        
        # Add last component if any
        if current_component and current_content:
            code_content = "\n".join(current_content).strip()
            if current_component in components:
                components[current_component]["content"] = code_content
                components[current_component]["file_type"] = current_file_type
            else:
                # Only store non-empty additional files
                if code_content and current_file_type:
                    additional_files.append({
                        "content": code_content,
                        "file_type": current_file_type,
                        "path": components.get(current_component, {}).get("path", "")
                    })
        
        # Filter out empty or invalid additional files
        additional_files = [
            f for f in additional_files 
            if f["content"] and f["file_type"] and not any(
                invalid in f["path"].lower() 
                for invalid in ["<summary>", "</summary>", "<param", "</param>", "<returns>", "</returns>"]
            )
        ]
        
        # Ensure all components have content
        if not any(c["content"] for c in components.values()) and not additional_files:
            raise ValueError("No code components were successfully parsed")
        
        # Log the components for debugging
        print("Generated components:")
        for key, value in components.items():
            print(f"{key}: {len(value['content'])} characters, type: {value['file_type']}, path: {value['path']}")
        print("Additional files:")
        for file in additional_files:
            print(f"Additional: {len(file['content'])} characters, type: {file['file_type']}, path: {file['path']}")
        
        # Return command with results
        return Command(
            goto="__end__",
            update={
                "_internal": {
                    **state["_internal"],
                    "output": {
                        "contract": components["contract"],  # Main contract implementation with metadata
                        "state": components["state"],  # State class implementation with metadata
                        "proto": components["proto"],  # Proto definitions with metadata
                        "reference": components["reference"],  # Reference code with metadata
                        "project": components["project"],  # Project configuration with metadata
                        "metadata": additional_files,  # Additional files with metadata
                        "analysis": analysis  # Analysis output
                    }
                }
            }
        )
        
    except Exception as e:
        error_msg = f"Error generating contract: {str(e)}"
        print(f"Generation error: {error_msg}")  # Add logging
        empty_code_file = {"content": "", "file_type": "", "path": ""}
        return Command(
            goto="__end__",
            update={
                "_internal": {
                    **state["_internal"],
                    "output": {
                        "contract": empty_code_file,
                        "state": empty_code_file,
                        "proto": empty_code_file,
                        "reference": empty_code_file,
                        "project": empty_code_file,
                        "metadata": [],  # Empty list for additional files
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
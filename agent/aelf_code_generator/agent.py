"""
This module defines the main agent workflow for AELF smart contract code generation.
"""

import os
import traceback
from typing import Dict, List, Any, Annotated, Literal
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.graph.message import add_messages
from langgraph.types import Command
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from aelf_code_generator.model import get_model
from aelf_code_generator.types import AgentState, ContractOutput, CodebaseInsight, get_default_state

# Define the internal state type with annotation for multiple updates
InternalStateType = Annotated[Dict, "internal"]

# Note: When using gemini-2.0-flash, system messages are converted to human messages
# This is handled by the ChatGoogleGenerativeAI class with convert_system_message_to_human=True

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

VALIDATION_PROMPT = """You are an expert AELF smart contract validator. Your task is to validate the generated smart contract code and identify potential issues before compilation.

Focus on these critical areas:

1. Protobuf Validation:
- Check for required AELF imports (aelf/options.proto)
- Verify correct namespace declarations
- Validate event message definitions
- Check service method signatures
- Verify proper use of repeated fields in messages

2. State Management:
- Verify state class naming consistency
- Check proper use of AELF state types (MappedState, SingletonState)
- Validate collection initialization patterns
- Verify state access patterns
- Check for proper state updates

3. Contract Implementation:
- Verify base class inheritance
- Check method implementations against protobuf definitions
- Validate event emission patterns
- Verify access control implementation
- Check pause mechanism implementation
- Ensure proper error handling
- Verify input validation

4. Security Checks:
- Verify input validation completeness
- Check state modification guards
- Validate owner-only functions
- Check for proper event emissions
- Verify authorization checks
- Check for reentrancy protection

5. Best Practices:
- Verify XML documentation completeness
- Check naming conventions
- Validate method visibility
- Check for code organization
- Verify error message clarity

Provide specific issues found and suggest fixes. If no issues are found, explicitly state "No issues found"."""

async def analyze_requirements(state: AgentState) -> Command[Literal["analyze_codebase", "__end__"]]:
    """Analyze the dApp description and provide detailed requirements analysis."""
    try:
        # Initialize internal state if not present
        if "generate" not in state or "_internal" not in state["generate"]:
            state["generate"] = {"_internal": get_default_state()["generate"]["_internal"]}
            
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
            
        # Create internal state with analysis
        internal_state = state["generate"]["_internal"]
        internal_state["analysis"] = analysis
        internal_state["output"] = {
            **internal_state.get("output", {}),
            "analysis": analysis
        }
        
        # Return command to move to next state
        return Command(
            goto="analyze_codebase",
            update={
                "generate": {
                    "_internal": internal_state
                }
            }
        )
        
    except Exception as e:
        print(f"Error in analyze_requirements: {str(e)}")
        print(f"Error traceback: {traceback.format_exc()}")
        
        # Initialize internal state if it doesn't exist
        if "generate" not in state or "_internal" not in state["generate"]:
            state["generate"] = {"_internal": get_default_state()["generate"]["_internal"]}
        
        # Create error state
        error_state = state["generate"]["_internal"]
        error_state["analysis"] = f"Error analyzing requirements: {str(e)}"
        error_state["output"] = {
            **error_state.get("output", {}),
            "analysis": f"Error analyzing requirements: {str(e)}"
        }
        
        # Return error state
        return Command(
            goto="__end__",
            update={
                "generate": {
                    "_internal": error_state
                }
            }
        )

async def analyze_codebase(state: AgentState) -> Command[Literal["generate_code", "__end__"]]:
    """Analyze AELF sample codebases to gather implementation insights."""
    try:
        # Initialize internal state if not present
        if "generate" not in state or "_internal" not in state["generate"]:
            state["generate"] = {"_internal": get_default_state()["generate"]["_internal"]}
            
        # Get analysis from internal state
        internal_state = state["generate"]["_internal"]
        analysis = internal_state.get("analysis", "")
        
        if not analysis:
            analysis = "No analysis provided. Proceeding with generic AELF contract implementation."
            internal_state["analysis"] = analysis
        
        # Identify relevant sample based on contract type
        contract_type = "smart contract"  # default
        relevant_samples = []
        
        # Determine contract type from analysis
        if "NFT" in analysis or "token" in analysis.lower():
            contract_type = "NFT contract"
            relevant_samples = ["nft"]
        elif "DAO" in analysis.lower():
            contract_type = "DAO contract"
            relevant_samples = ["simple-dao"]
        elif "game" in analysis.lower() or "lottery" in analysis.lower():
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
            SystemMessage(content=CODEBASE_ANALYSIS_PROMPT),
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
            
            # Update internal state with insights
            internal_state["codebase_insights"] = insights_dict
            
            # Return command to move to next state
            return Command(
                goto="generate_code",
                update={
                    "generate": {
                        "_internal": internal_state
                    }
                }
            )
                
        except Exception as e:
            print(f"Error analyzing codebase insights: {str(e)}")
            raise
            
    except Exception as e:
        print(f"Error in analyze_codebase: {str(e)}")
        print(f"Error traceback: {traceback.format_exc()}")
        
        # Initialize internal state if it doesn't exist
        if "generate" not in state or "_internal" not in state["generate"]:
            state["generate"] = {"_internal": get_default_state()["generate"]["_internal"]}
        
        # Create error state with default insights
        error_state = state["generate"]["_internal"]
        error_msg = f"Error analyzing codebase: {str(e)}"
        
        error_state["codebase_insights"] = {
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
        
        # Return command to continue to generate even if codebase analysis fails
        return Command(
            goto="generate_code",
            update={
                "generate": {
                    "_internal": error_state
                }
            }
        )

async def generate_contract(state: AgentState) -> Command[Literal["validate"]]:
    """Generate smart contract code based on analysis and codebase insights."""
    try:
        # Initialize internal state if not present
        if "generate" not in state or "_internal" not in state["generate"]:
            state["generate"] = {"_internal": get_default_state()["generate"]["_internal"]}
            
        # Get analysis and insights from internal state
        internal_state = state["generate"]["_internal"]
        analysis = internal_state.get("analysis", "")
        insights = internal_state.get("codebase_insights", {})
        fixes = internal_state.get("fixes", "")
        validation_count = internal_state.get("validation_count", 0)
        
        if not analysis:
            analysis = "No analysis provided. Proceeding with generic AELF contract implementation."
            internal_state["analysis"] = analysis
            
        if not insights:
            insights = {
                "project_structure": "Standard AELF project structure",
                "coding_patterns": "Common AELF patterns",
                "relevant_samples": ["hello-world"],
                "implementation_guidelines": "Follow AELF best practices"
            }
            internal_state["codebase_insights"] = insights
        
        # Get model with state
        model = get_model(state)
        
        # Generate code based on analysis and insights
        messages = [
            SystemMessage(content=CODE_GENERATION_PROMPT.format(
                implementation_guidelines=insights.get("implementation_guidelines", ""),
                coding_patterns=insights.get("coding_patterns", ""),
                project_structure=insights.get("project_structure", ""),
                relevant_samples="\n".join(insights.get("relevant_samples", []))
            )),
            HumanMessage(content=f"""
Analysis:
{analysis}

Previous Validation Issues and Fixes:
{fixes}

Please generate the complete smart contract implementation following AELF's project structure.
{f"This is iteration {validation_count + 1} of the code generation. Please incorporate the fixes suggested in the previous validation." if validation_count > 0 else ""}
""")
        ]
        
        try:
            # Set a longer timeout for code generation
            response = await model.ainvoke(messages, timeout=150)  # 5 minutes timeout
            content = response.content
            
            if not content:
                raise ValueError("Code generation failed - empty response")
        except TimeoutError:
            print("DEBUG - Code generation timed out, using partial response if available")
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
        
        # Extract contract name from file paths or content
        contract_name = None
        lines = content.split("\n")
        
        # First try to find contract name from class definition
        for line in lines:
            if "public class" in line and "Contract" in line and ":" in line:
                parts = line.split("public class")[1].strip().split(":")
                potential_name = parts[0].strip().replace("Contract", "")
                if potential_name and not any(x in potential_name.lower() for x in ["state", "reference", "test"]):
                    contract_name = potential_name
                    break
        
        # If not found, try file paths
        if not contract_name:
            for line in lines:
                if line.strip().startswith("//") and ".cs" in line and not any(x in line.lower() for x in ["state", "reference", "test"]):
                    file_path = line.replace("// ", "").strip()
                    if "/" in file_path:
                        potential_name = file_path.split("/")[-1].replace(".cs", "")
                        if potential_name and not any(x in potential_name.lower() for x in ["state", "reference", "test"]):
                            contract_name = potential_name
                            break
        
        # If still not found, use a default name
        if not contract_name:
            contract_name = "AELFContract"
            
        # Store contract name in components for consistent usage
        for component in components.values():
            component["contract_name"] = contract_name
            
        # Function to update paths and content with contract name
        def update_contract_name_references(content, path):
            """Helper function to consistently update contract name references."""
            if content:
                content = content.replace("ContractName", contract_name)
                content = content.replace("contractname", contract_name.lower())
                content = content.replace("namespace ContractName", f"namespace {contract_name}")
                
            if path:
                # Special handling for project file to ensure it's always named correctly
                if path.endswith(".csproj"):
                    path = f"src/{contract_name}.csproj"
                else:
                    path = path.replace("ContractName", contract_name)
                    path = path.replace("contractname", contract_name.lower())
                    
            return content, path

        # Initialize all file paths with correct names
        components["project"]["path"] = f"src/{contract_name}.csproj"
        components["contract"]["path"] = f"src/{contract_name}Contract.cs"
        components["state"]["path"] = f"src/{contract_name}State.cs"
        components["proto"]["path"] = f"src/Protobuf/contract/{contract_name.lower()}.proto"
        components["reference"]["path"] = "src/ContractReference.cs"

        # Parse code blocks
        current_component = None
        current_content = []
        in_code_block = False
        current_file_type = ""
        
        for i, line in enumerate(content.split("\n")):
            # Handle code block markers
            if "```" in line:
                if not in_code_block:
                    # Start of code block - detect language and file path
                    current_file_type = ""
                    if "csharp" in line.lower():
                        current_file_type = "csharp"
                    elif "protobuf" in line.lower() or "proto" in line.lower():
                        current_file_type = "proto"
                    elif "xml" in line.lower():
                        current_file_type = "xml"
                    
                    # Look for file path in next line
                    if i + 1 < len(content.split("\n")):
                        next_line = content.split("\n")[i + 1].strip()
                        if next_line.startswith("//") or next_line.startswith("<!--"):
                            file_path = (
                                next_line.replace("// ", "")
                                .replace("<!-- ", "")
                                .replace(" -->", "")
                                .strip()
                            )
                            
                            # Map file path to component type
                            if "State.cs" in file_path:
                                current_component = "state"
                            elif ".csproj" in file_path:
                                current_component = "project"
                            elif file_path.endswith(".cs") and "Reference" in file_path:
                                current_component = "reference"
                            elif ".proto" in file_path:
                                current_component = "proto"
                            elif file_path.endswith(".cs"):
                                current_component = "contract"
                            
                            if current_component:
                                components[current_component]["file_type"] = current_file_type
                else:
                    # End of code block
                    if current_component and current_content:
                        code_content = "\n".join(current_content).strip()
                        if current_component in components:
                            # Update content with contract name
                            code_content, _ = update_contract_name_references(code_content, "")
                            components[current_component]["content"] = code_content
                    current_content = []
                    current_component = None
                in_code_block = not in_code_block
                continue
            
            # Collect content if in a code block
            if in_code_block and current_component:
                current_content.append(line)

        # Create the output structure with metadata containing additional files
        output = {
            "contract": components["contract"],
            "state": components["state"],
            "proto": components["proto"],
            "reference": components["reference"],
            "project": components["project"],
            "metadata": additional_files,
            "analysis": analysis  # Preserve analysis in output
        }
        
        # Update internal state with output
        internal_state["output"] = output
        
        # Return command to move to validation
        return Command(
            goto="validate",
            update={
                "generate": {
                    "_internal": internal_state
                }
            }
        )
        
    except Exception as e:
        print(f"Error in generate_contract: {str(e)}")
        print(f"Error traceback: {traceback.format_exc()}")
        
        # Initialize internal state if it doesn't exist
        if "generate" not in state or "_internal" not in state["generate"]:
            state["generate"] = {"_internal": get_default_state()["generate"]["_internal"]}
        
        # Create error state
        error_state = state["generate"]["_internal"]
        error_msg = f"Error generating contract: {str(e)}"
        
        # Create empty code file
        empty_code_file = {"content": "", "file_type": "", "path": ""}
        
        # Update output with error
        error_state["output"] = {
            "contract": empty_code_file,
            "state": empty_code_file,
            "proto": empty_code_file,
            "reference": empty_code_file,
            "project": empty_code_file,
            "metadata": [],
            "analysis": error_msg
        }
        
        # Return error state
        return Command(
            goto="__end__",
            update={
                "generate": {
                    "_internal": error_state
                }
            }
        )

async def validate_contract(state: AgentState) -> Dict:
    """Validate the generated contract code and provide suggestions."""
    try:
        # Initialize internal state if not present
        if "generate" not in state:
            state["generate"] = {}
        if "_internal" not in state["generate"]:
            state["generate"]["_internal"] = get_default_state()["generate"]["_internal"]
        
        internal_state = state["generate"]["_internal"]
        current_count = internal_state.get("validation_count", 0)
        
        # Get the generated code from the state
        output = internal_state.get("output", {})
        
        contract_code = output.get("contract", {}).get("content", "")
        state_code = output.get("state", {}).get("content", "")
        proto_code = output.get("proto", {}).get("content", "")
        reference_code = output.get("reference", {}).get("content", "")
        project_code = output.get("project", {}).get("content", "")
        
        validation_results = []
        suggestions = []
        
        # Perform actual validation checks
        if contract_code:
            # Validate contract code
            if "public class" not in contract_code:
                validation_results.append("Contract class not properly defined")
                suggestions.append("Add proper public class definition inheriting from AElfContract")
            if "public override" not in contract_code:
                validation_results.append("Missing method overrides")
                suggestions.append("Implement required contract method overrides")
                
        if state_code:
            # Validate state code
            if "MappedState" not in state_code and "SingletonState" not in state_code:
                validation_results.append("Missing state definitions")
                suggestions.append("Add proper state variables using MappedState or SingletonState")
                
        if proto_code:
            # Validate proto definitions
            if "service" not in proto_code:
                validation_results.append("Missing service definition in proto")
                suggestions.append("Add proper service definition in proto file")
            if "message" not in proto_code:
                validation_results.append("Missing message definitions in proto")
                suggestions.append("Add required message definitions in proto file")
                
        # Create validation summary
        validation_summary = {
            "passed": len(validation_results) == 0,
            "issues": validation_results,
            "suggestions": suggestions
        }
        
        # Update internal state with validation results
        updated_internal = {
            **internal_state,
            "validation_count": current_count + 1,
            "validation_complete": True,
            "validation_result": validation_summary,
            "validation_status": "success" if len(validation_results) == 0 else "needs_improvement",
            "output": output  # Preserve the output structure
        }
        
        # Return state in the format expected by UI
        return {
            "generate": {
                "_internal": updated_internal
            }
        }
            
    except Exception as e:
        print(f"Error in validate_contract: {str(e)}")
        print(f"Error traceback: {traceback.format_exc()}")
        
        # Make sure we have internal_state defined even in case of error
        if not 'internal_state' in locals():
            internal_state = state.get("generate", {}).get("_internal", {})
            if not internal_state:
                internal_state = get_default_state()["generate"]["_internal"]
        
        # Preserve any existing output
        output = internal_state.get("output", {})
        
        # Create a default validation result
        validation_summary = {
            "passed": False,
            "issues": [f"Error during validation: {str(e)}"],
            "suggestions": ["Fix the validation errors and try again"]
        }
        
        # Return state in the format expected by UI
        return {
            "generate": {
                "_internal": {
                    **internal_state,
                    "validation_count": current_count + 1 if 'current_count' in locals() else 1,
                    "validation_complete": True,
                    "validation_result": validation_summary,
                    "validation_status": "error",
                    "output": output  # Preserve the output structure
                }
            }
        }

async def invoke_model(messages):
    """Helper function to invoke the model with messages."""
    try:
        # Get model
        model = get_model({"generate": {"_internal": {}}})
        
        # Convert dict messages to langchain messages
        lc_messages = []
        for msg in messages:
            if msg["role"] == "system":
                lc_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))
        
        # Invoke model
        print(f"DEBUG - invoke_model: Invoking model with {len(lc_messages)} messages")
        try:
            response = await model.ainvoke(lc_messages, timeout=180)  # 3 minutes timeout
            return response.content.strip()
        except TimeoutError:
            print("DEBUG - invoke_model: Model invocation timed out")
            return "Error: Model invocation timed out. Please try again."
    except Exception as e:
        print(f"Error invoking model: {str(e)}")
        print(f"Error traceback: {traceback.format_exc()}")
        return f"Error invoking model: {str(e)}"

def validation_router(state: AgentState) -> str:
    """
    Route to the appropriate next step based on validation results.
    Allows only one validation cycle before ending.
    """
    if "generate" not in state:
        state["generate"] = {}
    if "_internal" not in state["generate"]:
        state["generate"]["_internal"] = {}
            
    internal_state = state["generate"]["_internal"]
    current_count = internal_state.get("validation_count", 0)
    
    # If we have validation data, merge it into the main state
    if "validate" in state:
        validate_data = state.get("validate", {})
        if "generate" in validate_data and "_internal" in validate_data["generate"]:
            validate_internal = validate_data["generate"]["_internal"]
            
            # Copy validation data to main state
            for key in ["output", "validation_result", "validation_count", "validation_complete", "validation_status"]:
                if key in validate_internal:
                    internal_state[key] = validate_internal[key]
    
    # Ensure required fields exist
    if "output" not in internal_state:
        internal_state["output"] = {}
    if "validation_result" not in internal_state:
        internal_state["validation_result"] = {
            "passed": True,
            "issues": [],
            "suggestions": []
        }
    if "validation_status" not in internal_state:
        internal_state["validation_status"] = "success"
    
    # Allow only one validation cycle
    return "generate_code" if current_count == 0 else "__end__"

def create_agent() -> StateGraph:
    """Create the agent workflow with a linear flow and single validation cycle."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("analyze", analyze_requirements)
    workflow.add_node("analyze_codebase", analyze_codebase)
    workflow.add_node("generate_code", generate_contract)
    workflow.add_node("validate", validate_contract)
    
    # Set the entry point
    workflow.set_entry_point("analyze")

    # Define the linear flow
    workflow.add_edge("analyze", "analyze_codebase")
    workflow.add_edge("analyze_codebase", "generate_code")
    workflow.add_edge("generate_code", "validate")
    workflow.add_edge("generate_code", END)  # Add direct edge to END
    
    # Add conditional edges from validate
    workflow.add_conditional_edges(
        "validate",
        validation_router,
        {
            "generate_code": "generate_code",
            "__end__": END  # Use "__end__" as key and END constant as value
        }
    )
    
    return workflow.compile()

# Create the graph instance
graph = create_agent()

# Export
__all__ = ["graph", "get_default_state"] 
"""
This module defines the main agent workflow for AELF smart contract code generation.
"""

import os
import traceback
import re
import json
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

PROTO_GENERATION_PROMPT = """You are an expert AELF smart contract developer. Your task is to generate the content for an AELF-specific proto file.

Generate ONLY the content of the requested proto file. Do not include any explanations or markdown. The output should be valid proto syntax that can be directly saved to a file.

Proto file to generate: {proto_file_path}

For AELF proto files, follow these important guidelines:
1. Use the correct package name
2. Include proper csharp_namespace
3. Add comments explaining the purpose of each message, enum, or extension
4. Follow AELF's established structure and conventions for this file type
5. Include ALL required fields, options, and imports
6. Use correct field numbers for extensions

Example structure for aelf/options.proto:
- Extension for MethodOptions (is_view)
- Extended options for message fields (is_identity, behaves_like_collection, struct_type)
- Options for generating event code (csharp_namespace, base, controller)

Example structure for aelf/core.proto:
- Basic AELF types like Address, Hash
- Merkle path related structures
"""

async def generate_proto_file_content(model, proto_file_path: str) -> str:
    """Generate content for an AELF-specific proto file using the LLM."""
    try:
        # Generate proto file content using the LLM
        messages = [
            SystemMessage(content=PROTO_GENERATION_PROMPT.format(proto_file_path=proto_file_path)),
            HumanMessage(content=f"Please generate the content for the AELF proto file: {proto_file_path}")
        ]
        
        # Use a shorter timeout for proto generation - these are smaller files
        response = await model.ainvoke(messages, timeout=60)
        content = response.content.strip()
        
        if not content or "```" in content:
            # If the model returned markdown or empty content, clean it up
            content = content.replace("```protobuf", "").replace("```proto", "").replace("```", "").strip()
            
        if not content:
            print(f"Warning: LLM generated empty content for {proto_file_path}")
            # Generate minimal valid proto file with correct package name
            package_name = proto_file_path.split("/")[-1].replace(".proto", "")
            if "aelf/" in proto_file_path:
                package_name = "aelf"
            elif "acs" in proto_file_path:
                package_name = proto_file_path.split("/")[-1].replace(".proto", "")
            
            return f"""syntax = "proto3";

// This is a minimal placeholder generated for {proto_file_path}
// The LLM was unable to generate proper content
package {package_name};

// Please review and complete this proto file manually
"""
            
        return content
    except Exception as e:
        print(f"Error generating proto content for {proto_file_path}: {str(e)}")
        # Generate minimal valid proto file with package name derived from path
        package_name = proto_file_path.split("/")[-1].replace(".proto", "")
        if "aelf/" in proto_file_path:
            package_name = "aelf"
        elif "acs" in proto_file_path:
            package_name = proto_file_path.split("/")[-1].replace(".proto", "")
        
        return f"""syntax = "proto3";

// This is a minimal placeholder generated for {proto_file_path}
// Error during generation: {str(e)}
package {package_name};

// Please review and complete this proto file manually
"""

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
        
        # Get model to analyze requirements
        model = get_model(state)
        
        # Generate codebase insights with improved prompt
        messages = [
            SystemMessage(content=CODEBASE_ANALYSIS_PROMPT),
            HumanMessage(content=f"""
Based on the following contract requirements, provide implementation insights and patterns for an AELF smart contract.

Contract Requirements:
{analysis}

Please provide structured insights focusing on:

1. Project Structure and Organization
   - Required contract files and their purpose
   - State variables and their types
   - Events and their parameters
   - Contract references needed

2. Smart Contract Patterns
   - State management patterns
   - Access control patterns needed
   - Event handling patterns
   - Common utility functions
   - Error handling strategies

3. Implementation Guidelines
   - Best practices for AELF contracts
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
                project_structure=insights.get("project_structure", "")
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
            response = await model.ainvoke(messages, timeout=180)  # 3 minutes timeout
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
        found_components = set()  # Track which components we've already found
        contract_files = []  # Store all contract files (for multiple contract files)
        
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
                                # Check if we've already found a contract component
                                if "contract" in found_components:
                                    # This is an additional contract file
                                    current_component = f"additional_contract_{len(contract_files)}"
                                    contract_files.append({
                                        "content": "",
                                        "file_type": current_file_type,
                                        "path": file_path
                                    })
                                else:
                                    current_component = "contract"
                                    found_components.add("contract")
                            
                            if current_component:
                                if current_component.startswith("additional_contract_"):
                                    # For additional contract files, store the file path directly
                                    idx = int(current_component.split("_")[-1])
                                    contract_files[idx]["path"] = file_path
                                else:
                                    components[current_component]["file_type"] = current_file_type
                else:
                    # End of code block
                    if current_component and current_content:
                        code_content = "\n".join(current_content).strip()
                        if current_component.startswith("additional_contract_"):
                            # Store content for additional contract file
                            idx = int(current_component.split("_")[-1])
                            contract_files[idx]["content"] = code_content
                        elif current_component in components:
                            # Update content with contract name
                            code_content, _ = update_contract_name_references(code_content, "")
                            components[current_component]["content"] = code_content
                    current_content = []
                    current_component = None
                in_code_block = not in_code_block
                continue
            
            # Collect content if in a code block
            if in_code_block and current_component:
                # Skip the first line if it's a comment with the file path
                if len(current_content) == 0 and (line.startswith("// ") or line.startswith("<!-- ")):
                    if ("src/" in line or line.endswith(".cs") or line.endswith(".proto") or line.endswith(".csproj")):
                        continue
                current_content.append(line)

        # Add all additional contract files to metadata
        for contract_file in contract_files:
            content, path = update_contract_name_references(contract_file["content"], contract_file["path"])
            additional_files.append({
                "content": content,
                "file_type": contract_file["file_type"],
                "path": path
            })

        # Check the proto file for AELF-specific imports and generate additional proto files
        proto_content = components["proto"].get("content", "")
        if proto_content:
            # Parse the proto file for imports
            aelf_imports = []
            import_re = r'import\s+"([^"]+)";'
            imports = re.findall(import_re, proto_content)
            
            for import_path in imports:
                # Check if this is an AELF-specific import
                if import_path.startswith("aelf/"):
                    aelf_imports.append(import_path)
            
            # Generate content for AELF-specific imports
            for aelf_import in aelf_imports:
                import_path = f"src/Protobuf/reference/{aelf_import}"
                
                # Generate content using LLM instead of hardcoded templates
                import_content = await generate_proto_file_content(model, aelf_import)
                
                # Add to additional files if we have content
                if import_content:
                    additional_files.append({
                        "content": import_content,
                        "file_type": "proto",
                        "path": import_path
                    })
            
            # Check for ACS imports
            acs_imports = []
            for import_path in imports:
                if "acs" in import_path.lower():
                    acs_imports.append(import_path)
            
            # Generate content for ACS imports
            for acs_import in acs_imports:
                import_path = f"src/Protobuf/reference/{acs_import}"
                
                # Generate content using LLM instead of hardcoded templates
                import_content = await generate_proto_file_content(model, acs_import)
                
                # Add to additional files if we have content
                if import_content:
                    additional_files.append({
                        "content": import_content,
                        "file_type": "proto",
                        "path": import_path
                    })

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
        
        # Remove commented filenames from the beginning of the content
        for component_key in ["contract", "state", "proto", "reference", "project"]:
            component = output[component_key]
            content = component["content"]
            
            # If content starts with a commented filename, remove it
            if content:
                lines = content.split("\n")
                if lines and (
                    (lines[0].startswith("// src/") or lines[0].startswith("// Src/")) or
                    (lines[0].startswith("<!-- src/") or lines[0].startswith("<!-- Src/"))
                ):
                    component["content"] = "\n".join(lines[1:])
        
        # Remove contract_name fields from components in the output
        for component_key in ["contract", "state", "proto", "reference", "project"]:
            if "contract_name" in output[component_key]:
                del output[component_key]["contract_name"]
        
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
    """Validate the generated contract code and provide suggestions using LLM."""
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
        
        # Create a combined code representation for validation
        code_to_validate = f"""Main Contract File:
```csharp
{contract_code}
```

State Class File:
```csharp
{state_code}
```

Proto File:
```protobuf
{proto_code}
```

Reference Contract File:
```csharp
{reference_code}
```

Project File:
```xml
{project_code}
```"""

        # Get model with state
        model = get_model(state)
        
        # Generate validation using the LLM
        messages = [
            SystemMessage(content=VALIDATION_PROMPT),
            HumanMessage(content=f"""
Please validate the following smart contract code generated for AELF and provide a detailed analysis with specific issues and fixes:

{code_to_validate}

Categorize your findings into:
1. Critical issues (must be fixed)
2. Improvements (recommended but not critical)
3. Best practices

For each issue found, provide specific suggestions on how to fix it. If no issues are found in a category, explicitly state "No issues found in this category."
""")
        ]
        
        try:
            # Set timeout for validation
            validation_response = await model.ainvoke(messages, timeout=120)
            validation_feedback = validation_response.content.strip()
            
            if not validation_feedback:
                raise ValueError("Validation failed - empty response")
                
            # Basic parsing to extract issues and suggestions
            validation_results = []
            suggestions = []
            
            # Simple parsing logic - extract issues and suggestions
            lines = validation_feedback.split('\n')
            for i, line in enumerate(lines):
                if "issue" in line.lower() or "error" in line.lower() or "problem" in line.lower() or "missing" in line.lower():
                    validation_results.append(line.strip())
                    # Look for suggestion in the next few lines
                    for j in range(i+1, min(i+5, len(lines))):
                        if "fix" in lines[j].lower() or "suggestion" in lines[j].lower() or "should" in lines[j].lower() or "add" in lines[j].lower() or "change" in lines[j].lower():
                            suggestions.append(lines[j].strip())
                            break
            
            # If no explicit issues found but validation contains critical keywords
            if not validation_results:
                for critical_keyword in ["error", "missing", "invalid", "incorrect", "problem", "issue"]:
                    if critical_keyword in validation_feedback.lower():
                        validation_results.append(f"Potential issue detected: review '{critical_keyword}' mentions in validation")
                        break
            
            # Create validation summary
            validation_summary = {
                "passed": len(validation_results) == 0 or "no issues found" in validation_feedback.lower(),
                "issues": validation_results[:5],  # Limit to top 5 issues
                "suggestions": suggestions[:5]     # Limit to top 5 suggestions
            }
            
            # Update internal state with validation results and full feedback
            updated_internal = {
                **internal_state,
                "validation_count": current_count + 1,
                "validation_complete": True,
                "validation_result": validation_summary,
                "validation_status": "success" if validation_summary["passed"] else "needs_improvement",
                "output": output,  # Preserve the output structure
                "fixes": validation_feedback  # Store full validation feedback for next iteration
            }
            
            # Return state in the format expected by UI
            return {
                "generate": {
                    "_internal": updated_internal
                }
            }
                
        except Exception as e:
            print(f"Error during LLM validation: {str(e)}")
            print(f"Error traceback: {traceback.format_exc()}")
            raise
            
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
                    "output": output,  # Preserve the output structure
                    "fixes": f"Error during validation: {str(e)}\nPlease review the generated code and fix any apparent issues."
                }
            }
        }

async def test_contract(state: AgentState) -> Dict:
    """
    Test the generated contract by sending it to the AELF playground API.
    Handles build testing and code fixes internally for up to 2 iterations.
    
    This function:
    1. Creates a zip file from the generated contract files
    2. Sends the zip to the AELF playground API for build testing
    3. If build fails, passes errors to LLM to generate fixes
    4. Repeats the process up to 2 times if needed
    
    Args:
        state: The current state of the agent workflow
        
    Returns:
        A dictionary containing test results and any identified issues
    """
    import os
    import zipfile
    import json
    import tempfile
    import subprocess
    import base64
    
    # Initialize internal state if not present
    if "generate" not in state:
        state["generate"] = {}
    if "_internal" not in state["generate"]:
        state["generate"]["_internal"] = {}
    
    internal_state = state["generate"]["_internal"]
    
    # Get or initialize the test cycle count
    test_cycle_count = internal_state.get("test_cycle_count", 0)
    max_cycles = 2
    
    while test_cycle_count < max_cycles:
        internal_state["test_cycle_count"] = test_cycle_count + 1
        
        # Initialize test results for this iteration
        test_results = {
            "passed": False,
            "build_output": "",
            "errors": [],
            "warnings": [],
            "dll_output": "",
            "test_cycle": test_cycle_count + 1
        }
        
        try:
            # Get the output from the state
            output = internal_state.get("output", {})
            
            # Create a temporary directory to store the files
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create src directory
                src_dir = os.path.join(temp_dir, "src")
                os.makedirs(src_dir, exist_ok=True)
                
                # Extract contract, state and proto files from output
                files_to_write = []
                
                if "contract" in output and "content" in output["contract"]:
                    files_to_write.append({
                        "path": os.path.join(src_dir, os.path.basename(output["contract"].get("path", "Contract.cs"))),
                        "content": output["contract"]["content"]
                    })
                
                if "state" in output and "content" in output["state"]:
                    files_to_write.append({
                        "path": os.path.join(src_dir, os.path.basename(output["state"].get("path", "ContractState.cs"))),
                        "content": output["state"]["content"]
                    })
                
                if "proto" in output and "content" in output["proto"]:
                    # Create protobuf directory if it exists in the path
                    proto_path = output["proto"].get("path", "Protobuf/contract.proto")
                    proto_dir = os.path.dirname(proto_path)
                    if proto_dir:
                        os.makedirs(os.path.join(src_dir, proto_dir), exist_ok=True)
                    
                    files_to_write.append({
                        "path": os.path.join(src_dir, proto_path),
                        "content": output["proto"]["content"]
                    })
                
                # Add any additional files from output
                for key, value in output.items():
                    if key not in ["contract", "state", "proto"] and isinstance(value, dict) and "content" in value and "path" in value:
                        # Create directory if needed
                        file_dir = os.path.dirname(value["path"])
                        if file_dir:
                            os.makedirs(os.path.join(src_dir, file_dir), exist_ok=True)
                        
                        files_to_write.append({
                            "path": os.path.join(src_dir, value["path"]),
                            "content": value["content"]
                        })
                
                # Add metadata files (like aelf/options.proto and aelf/core.proto)
                metadata_files = output.get("metadata", [])
                for meta_file in metadata_files:
                    if isinstance(meta_file, dict) and "path" in meta_file and "content" in meta_file:
                        # Create directory if needed
                        file_dir = os.path.dirname(meta_file["path"])
                        if file_dir:
                            os.makedirs(os.path.join(src_dir, file_dir), exist_ok=True)
                        
                        files_to_write.append({
                            "path": os.path.join(src_dir, meta_file["path"]),
                            "content": meta_file["content"]
                        })
                
                # Write all files
                for file_info in files_to_write:
                    with open(file_info["path"], "w") as f:
                        f.write(file_info["content"])
                
                # Create the zip file
                zip_path = os.path.join(temp_dir, "src.zip")
                with zipfile.ZipFile(zip_path, "w") as zipf:
                    for root, _, files in os.walk(src_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arcname)
                
                # Send the zip file to the AELF playground API
                curl_cmd = [
                    "curl", "--location", "https://playground.aelf.com/playground/build",
                    "--form", f'contractFiles=@"{zip_path}"'
                ]
                
                # Execute the curl command
                process = subprocess.run(curl_cmd, capture_output=True, text=True)
                
                # Process the API response
                if process.returncode == 0:
                    response_text = process.stdout
                    
                    # Check if the response indicates build success (contains base64 DLL)
                    if not response_text.strip().startswith("TV") and "error" in response_text.lower():
                        # Build failed - extract error messages
                        test_results["passed"] = False
                        test_results["build_output"] = response_text
                        
                        # Parse error messages
                        error_lines = [line for line in response_text.split('\n') if "error" in line.lower()]
                        test_results["errors"] = error_lines
                        
                        # Parse warning messages
                        warning_lines = [line for line in response_text.split('\n') if "warning" in line.lower()]
                        test_results["warnings"] = warning_lines
                        
                        # If we have errors and haven't reached max cycles, try to fix them
                        if test_cycle_count < max_cycles:
                            # Prepare prompt for generating fixes
                            error_list = "\n".join(error_lines[:10])  # Limit to first 10 errors
                            
                            # Create a map of file extensions to their descriptions
                            file_type_descriptions = {
                                ".cs": "C# source code file",
                                ".csproj": "C# project file",
                                ".proto": "Protocol Buffer definition file"
                            }
                            
                            # Collect all files content for context
                            files_context = []
                            processed_files = set()  # Track already processed files
                            
                            # First add regular files from files_to_write
                            for file_info in files_to_write:
                                file_path = os.path.basename(file_info["path"])
                                if file_path in processed_files:
                                    continue  # Skip if already processed
                                
                                processed_files.add(file_path)
                                file_ext = os.path.splitext(file_info["path"])[1]
                                file_type = file_type_descriptions.get(file_ext, "source file")
                                files_context.append(f"""
                                File: {file_path} ({file_type})
                                Content:
                                {file_info["content"]}
                                """)
                            
                            # Then add metadata files, but only if not already processed
                            metadata_files = output.get("metadata", [])
                            for meta_file in metadata_files:
                                if isinstance(meta_file, dict) and "path" in meta_file and "content" in meta_file:
                                    filename = os.path.basename(meta_file["path"])
                                    if filename in processed_files:
                                        continue  # Skip if already processed
                                    
                                    processed_files.add(filename)
                                    file_ext = os.path.splitext(meta_file["path"])[1]
                                    file_type = file_type_descriptions.get(file_ext, "source file")
                                    files_context.append(f"""
                                    File: {filename} ({file_type})
                                    Content:
                                    {meta_file["content"]}
                                    """)
                            
                            files_content = "\n---\n".join(files_context)
                            
                            # Prepare the current output structure for the LLM
                            output_description = {
                                "contract": {
                                    "path": output.get("contract", {}).get("path", ""),
                                    "file_type": output.get("contract", {}).get("file_type", "")
                                },
                                "state": {
                                    "path": output.get("state", {}).get("path", ""),
                                    "file_type": output.get("state", {}).get("file_type", "")
                                },
                                "proto": {
                                    "path": output.get("proto", {}).get("path", ""),
                                    "file_type": output.get("proto", {}).get("file_type", "")
                                },
                                "reference": {
                                    "path": output.get("reference", {}).get("path", ""),
                                    "file_type": output.get("reference", {}).get("file_type", "")
                                },
                                "project": {
                                    "path": output.get("project", {}).get("path", ""),
                                    "file_type": output.get("project", {}).get("file_type", "")
                                },
                                "metadata_paths": [meta.get("path", "") for meta in output.get("metadata", []) if isinstance(meta, dict)]
                            }
                            
                            prompt = f"""
                            You are an expert AELF smart contract developer. The contract build has failed with the following errors:
                            
                            {error_list}
                            
                            Here are all the current contract files:
                            
                            {files_content}
                            
                            Please analyze these errors and generate fixes for the code. Focus on:
                            1. Missing or incorrect imports/using statements
                            2. Class inheritance and type issues
                            3. Static vs instance member declarations
                            4. Project file configuration issues
                            5. Proto file syntax and compatibility
                            6. Any syntax or compiler errors
                            
                            The current output structure is:
                            ```json
                            {json.dumps(output_description, indent=2)}
                            ```
                            
                            Instead of describing the changes, I want you to provide the complete updated output object 
                            that incorporates all necessary fixes. Return your response in the following format:
                            
                            <UPDATED_OUTPUT>
                            {{
                              "contract": {{
                                "content": "... complete updated content ...",
                                "path": "...",
                                "file_type": "..."
                              }},
                              "state": {{
                                "content": "... complete updated content ...",
                                "path": "...",
                                "file_type": "..."
                              }},
                              "proto": {{
                                "content": "... complete updated content ...",
                                "path": "...",
                                "file_type": "..."
                              }},
                              "reference": {{
                                "content": "... complete updated content ...",
                                "path": "...",
                                "file_type": "..."
                              }},
                              "project": {{
                                "content": "... complete updated content ...",
                                "path": "...",
                                "file_type": "..."
                              }},
                              "metadata": [
                                {{
                                  "content": "... complete updated content ...",
                                  "path": "...",
                                  "file_type": "..."
                                }},
                                ...
                              ]
                            }}
                            </UPDATED_OUTPUT>
                            
                            IMPORTANT: 
                            1. Include the COMPLETE content for each file, not just the changes.
                            2. Keep the same file paths and structure, just update the content to fix the build errors.
                            3. Ensure your response is valid JSON when extracted from the <UPDATED_OUTPUT> tags.
                            4. Make only the necessary changes to fix the build errors.
                            """
                            
                            # Call the model to generate fixes
                            model = get_model(state)
                            messages = [
                                SystemMessage(content="You are an expert AELF smart contract developer."),
                                HumanMessage(content=prompt)
                            ]
                            ai_response = await model.ainvoke(messages)
                            
                            # Store the suggested fixes
                            internal_state["suggested_fixes"] = ai_response.content
                            
                            # Parse the response to extract the updated output object
                            response_text = ai_response.content
                            debug_info = []  # Store debug info about the parsing process
                            
                            # Extract the updated output object
                            updated_output = None
                            match = re.search(r'<UPDATED_OUTPUT>(.*?)</UPDATED_OUTPUT>', response_text, re.DOTALL)
                            
                            if match:
                                try:
                                    # Extract and parse the JSON
                                    updated_output_str = match.group(1).strip()
                                    
                                    # Try to parse as JSON
                                    updated_output = json.loads(updated_output_str)
                                    
                                    # Validate the structure
                                    required_keys = ["contract", "state", "proto", "reference", "project", "metadata"]
                                    missing_keys = [key for key in required_keys if key not in updated_output]
                                    
                                    if missing_keys:
                                        # Try to keep the existing keys that are missing
                                        for key in missing_keys:
                                            if key in output:
                                                updated_output[key] = output[key]
                                    
                                    # Update the output with the LLM-generated complete object
                                    output = updated_output
                                    
                                except json.JSONDecodeError as e:
                                    # Try basic validation and sanitizing
                                    try:
                                        # Replace any problematic characters and try again
                                        sanitized_str = updated_output_str.replace('\t', '    ').replace('\\n', '\\\\n')
                                        updated_output = json.loads(sanitized_str)
                                        output = updated_output
                                    except:
                                        pass
                            
                            # Store debug info in internal state for troubleshooting if needed
                            internal_state["debug_info"] = debug_info
                            
                            # Update the state with fixed files
                            internal_state["output"] = output
                            
                            # Continue to next iteration
                            test_cycle_count += 1
                            continue
                            
                    else:
                        # Build successful
                        test_results["passed"] = True
                        test_results["build_output"] = "Build succeeded"
                        test_results["dll_output"] = response_text[:100] + "..." if len(response_text) > 100 else response_text
                        break  # Exit the loop on success
                else:
                    # API call failed
                    test_results["passed"] = False
                    test_results["build_output"] = f"API call failed: {process.stderr}"
                    test_results["errors"] = [process.stderr]
                    break  # Exit the loop on API failure
            
        except Exception as e:
            print(f"Error in test_contract: {str(e)}")
            print(f"Error traceback: {traceback.format_exc()}")
            
            # Update test results with error information
            test_results["passed"] = False
            test_results["build_output"] = f"Error during testing: {str(e)}"
            test_results["errors"] = [str(e)]
            break  # Exit the loop on exception
        
        test_cycle_count += 1
    
    # Store final test results in the state
    internal_state["test_results"] = test_results
    
    # Return the final state
    return {
        "generate": {
            "_internal": {
                "output": internal_state.get("output", {}),  # Keep only the essential output
                "analysis": internal_state.get("analysis", ""),  # Keep analysis for reference
                "fixes": internal_state.get("fixes", ""),  # Keep fixes information
                "codebase_insights": internal_state.get("codebase_insights", {}),  # Keep codebase insights
                "test_results": internal_state.get("test_results", {}),  # Keep test results
                "validation_results": internal_state.get("validation_result", {})  # Keep validation results
            }
        }
    }

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
    if "fixes" not in internal_state:
        internal_state["fixes"] = ""
    
    # Route to test_contract after successful validation
    # Store the current validation count for tracking retries
    internal_state["validation_count"] = current_count + 1
    
    if current_count < 2:
        # If we haven't reached the second validation yet, go back to generate_code
        return "generate_code"
    else:
        # After reaching validation_count of 2, proceed to test_contract
        # regardless of validation status
        return "test_contract"

def test_router(state: AgentState) -> str:
    """
    Route to end after test_contract completes.
    The test_contract function handles all iterations internally.
    """
    return "__end__"

def create_agent() -> StateGraph:
    """Create the agent workflow with a linear flow."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("analyze", analyze_requirements)
    workflow.add_node("analyze_codebase", analyze_codebase)
    workflow.add_node("generate_code", generate_contract)
    workflow.add_node("validate", validate_contract)
    workflow.add_node("test_contract", test_contract)
    
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
            "test_contract": "test_contract",
            "__end__": END
        }
    )
    
    # Add edge from test_contract to END
    workflow.add_edge("test_contract", END)
    
    return workflow.compile()

# Create the graph instance
graph = create_agent()

# Export
__all__ = ["graph", "get_default_state"] 
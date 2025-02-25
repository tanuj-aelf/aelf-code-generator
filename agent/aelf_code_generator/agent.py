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

# Define the internal state type with annotation for multiple updates
InternalStateType = Annotated[Dict, "internal"]

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
                },
                "validation_count": 0  # Initialize validation counter
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
        internal_state = {
            "analysis": analysis,
            "codebase_insights": state["_internal"]["codebase_insights"],
            "output": {
                "contract": "",
                "state": "",
                "proto": "",
                "analysis": analysis
            }
        }
        
        return Command(
            goto="analyze_codebase",
            update={
                "_internal": internal_state
            }
        )
        
    except Exception as e:
        error_msg = f"Error analyzing requirements: {str(e)}"
        error_state = {
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
        return Command(
            goto="__end__",
            update={
                "_internal": error_state
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
            
        # Create internal state dictionary
        internal_state = dict(state["_internal"])
        internal_state["codebase_insights"] = insights_dict
            
        # Return command to move to next state
        return Command(
            goto="generate",
            update={
                "_internal": internal_state
            }
        )
        
    except Exception as e:
        error_msg = f"Error analyzing codebase: {str(e)}"
        print(f"Codebase analysis error: {error_msg}")
        
        # Create error state dictionary
        error_state = dict(state["_internal"])
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
        
        return Command(
            goto="generate",  # Continue to generate even if codebase analysis fails
            update={
                "_internal": error_state
            }
        )

async def generate_contract(state: AgentState) -> Command[Literal["validate", "__end__"]]:
    """Generate smart contract code based on analysis and codebase insights."""
    try:
        # Get analysis and insights
        internal = state["_internal"]
        analysis = internal.get("analysis") or internal["output"]["analysis"]  # Try both locations
        insights = internal["codebase_insights"]
        fixes = internal.get("fixes", "")  # Get fixes if available
        
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
            HumanMessage(content=f"""
Analysis:
{analysis}

Previous Validation Issues and Fixes:
{fixes}

Please generate the complete smart contract implementation following AELF's project structure.""")
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
        
        # If still not found, try to extract from analysis
        if not contract_name and analysis:
            analysis_lower = analysis.lower()
            
            # First try to find explicit contract name
            if "contract name:" in analysis_lower:
                contract_line = [l for l in analysis.split("\n") if "contract name:" in l.lower()][0]
                potential_name = contract_line.split(":")[-1].strip()
                if potential_name and not any(x in potential_name.lower() for x in ["state", "reference", "test"]):
                    contract_name = potential_name
            
            # If still no name, ask the base model to suggest one based on the analysis
            if not contract_name:
                # Get model with state
                model = get_model(state)
                
                # Generate contract name based on analysis
                messages = [
                    SystemMessage(content="""You are an expert at naming AELF smart contracts. Based on the contract analysis provided, suggest a clear and descriptive contract name following these rules:
1. The name should reflect the contract's main purpose
2. Use PascalCase format
3. End with a relevant suffix (e.g., Contract, Manager, System)
4. Keep it concise but descriptive
5. Avoid generic terms like "Smart" or "Contract" alone
6. Do not include "AELF" or platform-specific prefixes
7. Exclude words like "State", "Reference", or "Test"

Return ONLY the suggested name, nothing else."""),
                    HumanMessage(content=f"Contract Analysis:\n{analysis}\n\nSuggest an appropriate name for this contract:")
                ]
                
                try:
                    response = await model.ainvoke(messages)
                    suggested_name = response.content.strip()
                    if suggested_name and not any(x in suggested_name.lower() for x in ["state", "reference", "test"]):
                        contract_name = suggested_name
                except Exception as e:
                    print(f"Error getting contract name suggestion: {str(e)}")
        
        if not contract_name:
            # If we still don't have a name, use a simple generic name
            contract_name = "ETF"
            
        # Debug log for contract name
        print(f"\nContract name determined: {contract_name}")
            
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

        # Move state content from contract to state if needed
        if components["state"]["content"] == "" and "State.cs" in components["contract"]["content"]:
            # Extract state content from contract
            state_content = ""
            lines = components["contract"]["content"].split("\n")
            state_start = -1
            state_end = -1
            
            for i, line in enumerate(lines):
                if "public class" in line and "State" in line:
                    state_start = i
                    # Find matching closing brace
                    brace_count = 1
                    for j in range(i + 1, len(lines)):
                        if "{" in lines[j]:
                            brace_count += 1
                        if "}" in lines[j]:
                            brace_count -= 1
                        if brace_count == 0:
                            state_end = j + 1
                            break
                    break
            
            if state_start != -1 and state_end != -1:
                state_content = "\n".join(lines[state_start-1:state_end])  # Include namespace
                components["state"]["content"] = state_content
                # Remove state content from contract
                components["contract"]["content"] = "\n".join(lines[:state_start-1] + lines[state_end:])

        # Create the output structure with metadata containing additional files
        output = {
            "contract": {
                "content": components["contract"]["content"],
                "file_type": components["contract"]["file_type"],
                "path": components["contract"]["path"]
            },
            "state": {
                "content": components["state"]["content"],
                "file_type": components["state"]["file_type"],
                "path": components["state"]["path"]
            },
            "proto": {
                "content": components["proto"]["content"],
                "file_type": components["proto"]["file_type"],
                "path": components["proto"]["path"]
            },
            "reference": {
                "content": components["reference"]["content"],
                "file_type": components["reference"]["file_type"],
                "path": components["reference"]["path"]
            },
            "project": {
                "content": components["project"]["content"],
                "file_type": components["project"]["file_type"],
                "path": components["project"]["path"]
            },
            "metadata": [
                {
                    "content": file["content"],
                    "file_type": file["file_type"],
                    "path": file["path"]
                }
                for file in additional_files
                if not any(
                    invalid in file["path"].lower()
                    for invalid in ["<summary>", "</summary>", "<param", "</param>", "<returns>", "</returns>"]
                )
            ],
            "analysis": analysis  # Preserve analysis in output
        }
        
        # Create internal state dictionary
        internal_state = dict(state["_internal"])
        internal_state.update({
            "analysis": analysis,  # Preserve analysis at top level
            "output": output,
            "validation_count": internal.get("validation_count", 0)  # Preserve validation count
        })
        
        # Return command to move to validation
        return Command(
            goto="validate",
            update={
                "_internal": internal_state
            }
        )
        
    except Exception as e:
        error_msg = f"Error generating contract: {str(e)}"
        print(f"Generation error: {error_msg}")
        
        # Create error state dictionary
        error_state = dict(state["_internal"])
        error_state.update({
            "analysis": state["_internal"].get("analysis") or state["_internal"]["output"]["analysis"],  # Preserve analysis
            "output": {
                "contract": empty_code_file,
                "state": empty_code_file,
                "proto": empty_code_file,
                "reference": empty_code_file,
                "project": empty_code_file,
                "metadata": [],
                "analysis": error_msg
            }
        })
        
        return Command(
            goto="__end__",
            update={
                "_internal": error_state
            }
        )

async def validate_contract(state: AgentState) -> Command[Literal["generate", "__end__"]]:
    """Validate the generated contract code and suggest fixes. Maximum of 1 validation iteration allowed."""
    try:
        # Get the generated code from state
        internal = state["_internal"]
        output = internal["output"]
        contract_code = output["contract"]["content"]
        state_code = output["state"]["content"]
        proto_code = output["proto"]["content"]
        analysis = internal.get("analysis") or output["analysis"]  # Try both locations
        
        # Get model for validation
        model = get_model(state)
        
        # Prepare validation messages
        messages = [
            SystemMessage(content=VALIDATION_PROMPT),
            HumanMessage(content=f"""
Please validate the following AELF smart contract code:

Proto File:
{proto_code}

State Class:
{state_code}

Contract Implementation:
{contract_code}

Identify any issues that would prevent successful compilation or cause runtime issues.""")
        ]
        
        # Get validation response
        response = await model.ainvoke(messages)
        validation_result = response.content.strip()
        
        # If issues found, get fixes
        if "No issues found" not in validation_result:
            fix_messages = [
                SystemMessage(content="You are an expert AELF smart contract developer. Based on the validation issues found, provide specific code fixes."),
                HumanMessage(content=f"""
Validation found the following issues:
{validation_result}

Please provide specific code fixes for each file:""")
            ]
            
            fix_response = await model.ainvoke(fix_messages)
            fixes = fix_response.content.strip()
        else:
            fixes = ""
            
        # Increment validation count
        validation_count = internal.get("validation_count", 0) + 1
        print(f"Validation iteration {validation_count} completed.")
        
        # Create updated state dictionary
        updated_state = dict(internal)
        updated_state.update({
            "analysis": analysis,  # Preserve analysis
            "validation_count": validation_count,
            "validation_result": validation_result,
            "fixes": fixes,
            "output": {
                **output,
                "validation_result": validation_result,
                "fixes": fixes
            }
        })
        
        # Return command with updated state
        return Command(
            goto="generate" if validation_count < 1 and "No issues found" not in validation_result else "__end__",
            update={
                "_internal": updated_state
            }
        )
        
    except Exception as e:
        error_msg = f"Error in validation: {str(e)}"
        print(f"Validation error: {error_msg}")
        
        # Create error state dictionary
        error_state = dict(state["_internal"])
        error_state["output"] = {
            **state["_internal"]["output"],
            "validation_error": error_msg
        }
        
        return Command(
            goto="__end__",
            update={
                "_internal": error_state
            }
        )

def create_agent() -> StateGraph:
    """Create the agent workflow with a clean, linear flow and proper validation cycle."""
    # Create a new graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("analyze", analyze_requirements)
    workflow.add_node("analyze_codebase", analyze_codebase)
    workflow.add_node("generate", generate_contract)
    workflow.add_node("validate", validate_contract)

    # Add conditional node for validation cycle
    async def should_continue_validation(state: AgentState) -> bool:
        """Helper function to determine if validation should continue."""
        validation_count = state["_internal"].get("validation_count", 0)
        validation_result = state["_internal"].get("validation_result", "")
        return validation_count < 1 and "No issues found" not in validation_result

    # Set the entry point
    workflow.set_entry_point("analyze")

    # Define the main linear flow
    workflow.add_edge("analyze", "analyze_codebase")
    workflow.add_edge("analyze_codebase", "generate")
    workflow.add_edge("generate", "validate")
    
    # Add conditional edges from validate
    workflow.add_conditional_edges(
        "validate",
        should_continue_validation,
        {
            True: "generate",  # Continue validation cycle
            False: END  # End the flow
        }
    )
    
    # Compile the graph
    return workflow.compile()

# Create the graph instance
graph = create_agent()

# Export
__all__ = ["graph", "get_default_state"] 
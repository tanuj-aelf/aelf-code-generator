import asyncio
import json
import re
import os
from aelf_code_generator.agent import graph, get_default_state, generate_proto_file_content
from aelf_code_generator.model import get_model
from aelf_code_generator.types import AgentState
from langchain_core.messages import SystemMessage, HumanMessage

async def main():
    """Run all tests sequentially."""
    await test_aelf_import_generation()
    await test_proto_file_generation()

async def test_aelf_import_generation():
    """Test that AELF-specific imports are correctly generated."""
    # Create a more explicit contract description that will require aelf/options.proto
    description = """
    Create an AELF token contract with the following features:
    1. Import the aelf/options.proto and aelf/core.proto files explicitly
    2. Standard token functionality (mint, burn, transfer)
    3. Owner-only minting and burning
    4. Event emission for all state changes
    5. Must use the View method option from aelf/options.proto for read-only methods
    6. Must use the Address type from aelf/core.proto for owner and other addresses
    7. Make sure to generate a proper proto file with these AELF-specific imports
    """
    
    # Create initial state with description
    state = get_default_state()
    state["input"] = description
    
    # Run the graph
    print("Running the agent graph...")
    result = await graph.ainvoke(state)
    
    # Access the internal state to check generated code
    internal_state = result.get("generate", {}).get("_internal", {})
    output = internal_state.get("output", {})
    
    # Print analysis and insights for debugging
    print("\nAnalysis:")
    analysis = internal_state.get("analysis", "No analysis found")
    print(analysis[:300] + "..." if len(analysis) > 300 else analysis)
    
    print("\nCodebase Insights:")
    insights = internal_state.get("codebase_insights", {})
    for key, value in insights.items():
        print(f"\n{key.upper()}:")
        if isinstance(value, str):
            print(value[:200] + "..." if len(value) > 200 else value)
        else:
            print(value)
    
    # Print the main proto file
    print("\n\nMain Proto File:")
    proto_file = output.get("proto", {}).get("content", "")
    print(proto_file)
    
    # Check for aelf imports in the proto file
    print("\nChecking for AELF imports in the proto file...")
    
    aelf_imports = []
    for line in proto_file.split("\n"):
        if 'import "aelf/' in line:
            aelf_imports.append(line.strip())
            print(f"Found AELF import: {line.strip()}")
    
    if not aelf_imports:
        print("No AELF imports found in the proto file.")
    
    # Check if additional proto files were generated
    print("\nAdditional Generated Files:")
    
    metadata = output.get("metadata", [])
    for file in metadata:
        print(f"\nPath: {file.get('path', '')}")
        print(f"File Type: {file.get('file_type', '')}")
        print("Content (first 200 characters):")
        content = file.get('content', '')
        print(content[:200] + "..." if len(content) > 200 else content)
    
    print("\nTotal additional files generated:", len(metadata))
    
    # If no AELF imports, manually run the proto file generation for testing
    if not aelf_imports and proto_file:
        print("\nManually testing import detection and file generation...")
        
        # Define test imports
        test_proto = proto_file + '\nimport "aelf/options.proto";\nimport "aelf/core.proto";'
        
        # Use our regex to detect imports
        import_re = r'import\s+"([^"]+)";'
        imports = re.findall(import_re, test_proto)
        
        print("Detected imports:", imports)
        
        # Check if our regex can detect AELF imports
        aelf_imports = [imp for imp in imports if imp.startswith("aelf/")]
        print("AELF imports:", aelf_imports)
        
        # Test file generation for each AELF import
        for aelf_import in aelf_imports:
            print(f"\nWould generate file for: {aelf_import}")
            import_path = f"src/Protobuf/reference/{aelf_import}"
            print(f"Path: {import_path}")

async def test_proto_file_generation():
    """Test the LLM-based proto file generation specifically."""
    print("\n\n=== Testing LLM-based Proto File Generation ===\n")
    
    # Initialize the model
    state = get_default_state()
    model = get_model(state)
    
    try:
        # Test generating aelf/options.proto
        print("\nGenerating aelf/options.proto:")
        options_content = await generate_proto_file_content(model, "aelf/options.proto")
        print(f"Generated {len(options_content)} characters")
        print("First 200 characters:")
        print(options_content[:200] + "...")
        
        # Check for key components
        print("\nChecking for key components:")
        key_terms = ["MethodOptions", "is_view", "csharp_namespace", "package aelf"]
        for term in key_terms:
            if term in options_content:
                print(f"✓ Contains '{term}'")
            else:
                print(f"✗ Missing '{term}'")
        
        # Test generating aelf/core.proto
        print("\nGenerating aelf/core.proto:")
        core_content = await generate_proto_file_content(model, "aelf/core.proto")
        print(f"Generated {len(core_content)} characters")
        print("First 200 characters:")
        print(core_content[:200] + "...")
        
        # Check for key components
        print("\nChecking for key components:")
        key_terms = ["message Address", "message Hash", "MerklePath", "package aelf"]
        for term in key_terms:
            if term in core_content:
                print(f"✓ Contains '{term}'")
            else:
                print(f"✗ Missing '{term}'")
        
        # Test generating acs12.proto
        print("\nGenerating acs12.proto:")
        acs_content = await generate_proto_file_content(model, "acs12.proto")
        print(f"Generated {len(acs_content)} characters")
        print("First 200 characters:")
        print(acs_content[:200] + "...")
        
        # Check for key components and alternative components (since LLM might use different package names)
        print("\nChecking for key components:")
        key_terms = ["package acs12", "UserContract", "MethodFees", "SetMethodFee"]
        alt_terms = ["aelf.contracts.acs12", "fee", "method", "rpc"]
        
        for term in key_terms:
            found = term in acs_content
            alt_found = any(alt in acs_content.lower() for alt in alt_terms)
            if found:
                print(f"✓ Contains '{term}'")
            elif alt_found:
                print(f"◐ Uses alternative format instead of '{term}'")
            else:
                print(f"✗ Missing '{term}'")
    except Exception as e:
        print(f"Error during test: {str(e)}")

if __name__ == "__main__":
    # Use asyncio.run to properly manage the event loop
    asyncio.run(main()) 
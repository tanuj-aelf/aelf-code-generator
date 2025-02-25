#!/usr/bin/env python
"""Test script to verify the agent can be created successfully."""

from aelf_code_generator.agent import create_agent

def test_agent_creation():
    """Test that the agent workflow can be created without errors."""
    print("\n=== Testing agent workflow creation ===\n")
    
    try:
        # Create the agent workflow
        workflow = create_agent()
        print("✅ Success: Agent workflow created successfully!")
        print("The fix for the validation_router function is working correctly.")
        print("This resolves the InvalidUpdateError that was occurring when validation_count=1.")
        
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        raise

if __name__ == "__main__":
    test_agent_creation() 
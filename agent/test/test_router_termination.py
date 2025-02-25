#!/usr/bin/env python
"""Test script to verify the validation_router correctly terminates the workflow."""

import asyncio
import sys
from aelf_code_generator.agent import validation_router, create_agent
from aelf_code_generator.types import get_default_state, AgentState
from langgraph.types import Command

async def test_validation_router_termination():
    """
    Directly test that the validation_router function correctly terminates 
    the workflow when validation_count is 1.
    """
    print("\n=== Testing validation_router termination ===\n")
    
    # Create a test state that exactly matches what we'd see in the real workflow
    # after validation completes
    test_state = get_default_state()
    test_state["generate"]["_internal"]["validation_count"] = 1
    test_state["generate"]["_internal"]["validation_complete"] = True
    test_state["generate"]["_internal"]["validation_result"] = "Max validation iterations reached"
    test_state["generate"]["_internal"]["fixes"] = "No more fixes attempted - max iterations reached"
    
    print(f"Test state created with: validation_count=1, validation_complete=True")
    
    # Call the validation_router directly with our test state
    print("Calling validation_router with this state...")
    result = validation_router(test_state)
    
    # Check the result
    print(f"\nValidation router returned: {result}")
    
    if isinstance(result, Command) and result.goto == "__end__":
        print("\n✅ PASS: validation_router correctly returned Command(goto='__end__')")
    else:
        print(f"\n❌ FAIL: validation_router returned {result}, not Command(goto='__end__')")
        return False
    
    # Now test the full workflow creation to ensure it's structurally sound
    print("\nCreating agent workflow to check graph structure...")
    try:
        workflow = create_agent()
        print("✅ PASS: Agent workflow created successfully!")
        print("The validation_router is correctly connected in the graph.")
        return True
    except Exception as e:
        print(f"❌ FAIL: Error creating agent workflow: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_validation_router_termination())
    sys.exit(0 if success else 1) 
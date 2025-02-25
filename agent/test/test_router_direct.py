#!/usr/bin/env python
"""Direct test for the validation_router function to verify it returns the correct Command."""

import sys
from pprint import pprint
from aelf_code_generator.agent import validation_router
from aelf_code_generator.types import get_default_state
from langgraph.types import Command

async def test_validation_router_direct():
    """
    Directly call the validation_router function with a controlled state to verify 
    it returns the expected Command(goto='__end__') when validation_count=1.
    """
    print("\n=== Testing validation_router function directly ===\n")
    
    # Create a test state with validation_count=1 and validation_complete=True
    state = get_default_state()
    if "generate" not in state:
        state["generate"] = {}
    if "_internal" not in state["generate"]:
        state["generate"]["_internal"] = {}
    
    # Set the critical state values that should trigger termination
    state["generate"]["_internal"]["validation_count"] = 1
    state["generate"]["_internal"]["validation_complete"] = True
    state["generate"]["_internal"]["validation_result"] = "Validation complete"
    
    print("Test state prepared:")
    print(f"  validation_count = {state['generate']['_internal']['validation_count']}")
    print(f"  validation_complete = {state['generate']['_internal']['validation_complete']}")
    
    try:
        # Call the validation_router function directly
        print("\nCalling validation_router...")
        result = await validation_router(state)
        
        # Verify the result
        print("\nResult:", result)
        
        # Check if result is a Command
        is_command = isinstance(result, Command)
        print(f"Is Command instance: {is_command}")
        
        # Check if result has goto attribute
        has_goto = hasattr(result, "goto")
        print(f"Has goto attribute: {has_goto}")
        
        # Check if goto value is __end__
        if has_goto:
            goto_value = result.goto
            print(f"goto value: {goto_value}")
            is_end = goto_value == "__end__"
            print(f"goto is __end__: {is_end}")
        
        # Final assessment
        if is_command and has_goto and goto_value == "__end__":
            print("\n✅ PASS: validation_router correctly returns Command(goto='__end__')")
            return True
        else:
            print("\n❌ FAIL: validation_router does not return the expected Command")
            return False
    
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_validation_router_direct())
    sys.exit(0 if success else 1) 
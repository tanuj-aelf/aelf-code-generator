#!/usr/bin/env python
"""Test the validation_router function with a simplified setup."""

import sys
import asyncio
from aelf_code_generator.agent import validation_router
from aelf_code_generator.types import get_default_state
from langgraph.types import Command

async def test_validation_router():
    """Test the validation_router with a controlled state."""
    print("\n=== Testing validation_router with validation_count=1 ===\n")
    
    # Set up test state
    state = get_default_state()
    state["generate"] = {"_internal": {}}
    state["generate"]["_internal"]["validation_count"] = 1
    state["generate"]["_internal"]["validation_complete"] = True
    
    print("Test state:")
    print(f"  validation_count = {state['generate']['_internal']['validation_count']}")
    print(f"  validation_complete = {state['generate']['_internal']['validation_complete']}")
    
    # Call the validation_router
    print("\nCalling validation_router...")
    try:
        result = await validation_router(state)
        print(f"Result: {result}")
        
        # Check if result is correct
        is_correct = isinstance(result, Command) and result.goto == "__end__"
        if is_correct:
            print("\n✅ PASS: validation_router returned Command(goto='__end__')")
            return True
        else:
            print("\n❌ FAIL: validation_router did not return the expected result")
            print(f"Expected: Command(goto='__end__'), Got: {result}")
            return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_validation_router())
    sys.exit(0 if success else 1) 
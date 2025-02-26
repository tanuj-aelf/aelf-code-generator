#!/usr/bin/env python
"""Test script to directly test validation_router termination by setting it as entry point."""

import asyncio
import time
import sys
import json
from pprint import pprint
from langgraph.graph import StateGraph, END
from langgraph.types import Command
from aelf_code_generator.agent import validation_router
from aelf_code_generator.types import get_default_state, AgentState

async def test_direct_validation_router():
    """
    Test the validation_router directly by setting it as the entry point of a StateGraph.
    This is a focused test to ensure termination works correctly.
    """
    print("\n=== Testing direct validation_router termination ===\n")
    
    # Create a minimal workflow with only validation_router
    workflow = StateGraph(AgentState)
    workflow.add_node("validation_router", validation_router)
    # Skip all normal nodes and set validation_router as entry point
    workflow.set_entry_point("validation_router")
    # Connect to both possible destinations
    workflow.add_edge("validation_router", "generate_code")
    workflow.add_edge("validation_router", END)
    
    # Add a dummy node for "generate_code" (won't be used but needed for edge)
    def dummy_generate(*args, **kwargs):
        # This shouldn't be called
        print("UNEXPECTED: dummy_generate was called!")
        return {}
    
    workflow.add_node("generate_code", dummy_generate)
    
    # Compile the workflow
    agent = workflow.compile()
    
    # Create a state with validation_count=1 to trigger termination
    state = get_default_state()
    if "generate" not in state:
        state["generate"] = {}
    if "_internal" not in state["generate"]:
        state["generate"]["_internal"] = {}
    state["generate"]["_internal"]["validation_count"] = 1
    state["generate"]["_internal"]["validation_complete"] = True
    
    print(f"Starting with state: validation_count={state['generate']['_internal']['validation_count']}, validation_complete={state['generate']['_internal']['validation_complete']}")
    
    # Set up tracking variables
    executed_nodes = []
    reached_end = False
    max_steps = 30
    step_count = 0
    
    print("\nExecuting the direct validation_router workflow...")
    print("-" * 50)
    
    try:
        # Stream events to track node execution
        async for event in agent.astream_events(state, stream_mode="node", version="v1"):
            step_count += 1
            
            # Print full event for better debugging
            print(f"\nSTEP {step_count} EVENT:")
            pprint(event)
            
            # Process node events
            node_name = event.get("node")
            status = event.get("status", "unknown")
            
            if status == "start" and node_name not in executed_nodes:
                executed_nodes.append(node_name)
                print(f"Executing node: {node_name}")
            
            # If we're at validation_router, print the debug info
            if node_name == "validation_router" and status == "start":
                print("\nVALIDATION ROUTER STATE:")
                if "state" in event:
                    try:
                        state_data = event["state"]
                        internal_state = state_data.get("generate", {}).get("_internal", {})
                        validation_count = internal_state.get("validation_count", "Not found")
                        validation_complete = internal_state.get("validation_complete", "Not found")
                        print(f"validation_count: {validation_count}")
                        print(f"validation_complete: {validation_complete}")
                    except Exception as e:
                        print(f"Error extracting state: {e}")
            
            # If we're at 'end' status of validation_router, see what direction it's going
            if node_name == "validation_router" and status == "end":
                print("Validation router completed - where are we going next?")
                if "result" in event:
                    print(f"Result from validation_router: {event['result']}")
                
            # Check for workflow completion
            if node_name == "__end__" and status == "start":
                reached_end = True
                print("\n✅ Workflow successfully reached __end__ node!")
                break
    except Exception as e:
        print(f"❌ FAIL: Error during workflow execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    print("-" * 50)
    print(f"Executed nodes: {' -> '.join(executed_nodes)}")
    
    # Final verification
    if reached_end:
        print("\n✅ PASS: Workflow correctly terminated after validation_router")
        return True
    else:
        print("\n❌ FAIL: Workflow did not reach the __end__ node")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_direct_validation_router())
    sys.exit(0 if success else 1) 
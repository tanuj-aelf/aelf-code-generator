#!/usr/bin/env python
"""Test script to verify the agent workflow properly terminates after validation."""

import asyncio
import time
import sys
import json
from pprint import pprint
from aelf_code_generator.agent import create_agent
from aelf_code_generator.types import get_default_state, AgentState

async def test_full_workflow_termination():
    """
    Test the entire agent workflow to ensure it correctly terminates after validation.
    This test simulates a complete workflow execution and checks that it reaches the __end__ node.
    """
    print("\n=== Testing full agent workflow termination ===\n")
    
    # Create the agent workflow
    try:
        workflow = create_agent()
        print("✅ Agent workflow created successfully!")
    except Exception as e:
        print(f"❌ FAIL: Error creating agent workflow: {str(e)}")
        return False
    
    # Create a minimal starting state to avoid complex analysis
    state = get_default_state()
    state["input"] = "Create a simple Hello World contract for AELF"
    
    # Set validation_count=1 to trigger immediate termination via validation_router
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
    max_steps = 15  # Increased safety limit
    step_count = 0
    
    print("\nExecuting the workflow with minimal input...")
    print("-" * 50)
    
    try:
        # Add debugging to see if validation_router is properly initialized with a goto=END edge
        print("Workflow nodes and edges:")
        print("Nodes:", getattr(workflow, "nodes", "Not accessible"))
        
        # Stream events to track node execution
        async for event in workflow.astream_events(state, stream_mode="node", version="v1"):
            step_count += 1
            
            # Print full event for debugging
            print(f"\nSTEP {step_count} EVENT:")
            pprint(event)
            
            # Process node events
            node_name = event.get("node")
            status = event.get("status", "unknown")
            
            if status == "start" and node_name not in executed_nodes:
                executed_nodes.append(node_name)
                print(f"Executing node: {node_name}")
                
                # If we're at validation_router, print the state for debugging
                if node_name == "validation_router":
                    print("\nVALIDATION ROUTER STATE:")
                    if "state" in event:
                        # Print key validation state values
                        try:
                            state_data = event["state"]
                            internal_state = state_data.get("generate", {}).get("_internal", {})
                            validation_count = internal_state.get("validation_count", "Not found")
                            validation_complete = internal_state.get("validation_complete", "Not found")
                            print(f"validation_count: {validation_count}")
                            print(f"validation_complete: {validation_complete}")
                        except Exception as e:
                            print(f"Error extracting state: {e}")
            
            # If we're at 'end' status of validation_router, show where we're going next
            if node_name == "validation_router" and status == "end":
                print("Validation router completed - checking next node")
            
            # Check for workflow completion
            if node_name == "__end__" and status == "start":
                reached_end = True
                print("\n✅ Workflow successfully reached __end__ node!")
                break
                
            # Safety termination
            if step_count >= max_steps:
                print(f"\n⚠️ Reached maximum steps ({max_steps}) without terminating")
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
        print("\n✅ PASS: Workflow correctly terminated after validation")
        return True
    else:
        print("\n❌ FAIL: Workflow did not reach the __end__ node")
        # Try to analyze why it didn't terminate
        if "validation_router" in executed_nodes:
            index = executed_nodes.index("validation_router")
            if index < len(executed_nodes) - 1:
                print(f"After validation_router, workflow went to: {executed_nodes[index+1]}")
                print("This suggests the Command(goto='__end__') is not being honored")
            else:
                print("validation_router was the last node executed before hitting step limit")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_full_workflow_termination())
    sys.exit(0 if success else 1) 
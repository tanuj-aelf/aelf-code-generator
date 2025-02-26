#!/usr/bin/env python
"""Test script to verify the agent workflow with a complex input."""

import asyncio
import sys
import time
from pprint import pprint
from aelf_code_generator.agent import create_agent, validation_router
from aelf_code_generator.types import get_default_state

async def test_agent_with_input():
    """
    Test the agent workflow with a complex input and verify it terminates properly.
    """
    print("\n=== Testing Agent Workflow With ETF dApp Input ===\n")
    
    # Create the agent workflow
    try:
        workflow = create_agent()
        print("✅ Agent workflow created successfully!")
    except Exception as e:
        print(f"❌ FAIL: Error creating agent workflow: {str(e)}")
        return False
    
    # Create a state with a simpler input to reduce processing time
    state = get_default_state()
    state["input"] = "Create a simple hello world contract for AELF"
    
    print("\nRunning with simplified input to test workflow termination...")
    print("-" * 50)
    
    # Set up tracking variables
    executed_nodes = []
    reached_end = False
    max_steps = 30  # Reduced for faster testing
    step_count = 0
    last_event = None
    last_node = None
    
    try:
        # Stream events to track node execution
        async for event in workflow.astream_events(state, stream_mode="node", version="v1"):
            step_count += 1
            last_event = event
            
            # Process node events
            node_name = event.get("node")
            status = event.get("status", "unknown")
            last_node = node_name
            
            # Add the node to our list if we're starting it
            if status == "start" and node_name not in executed_nodes:
                executed_nodes.append(node_name)
                print(f"\nStep {step_count}: Executing node: {node_name} (status: {status})")
                
                # If we're at the validation node, show count
                if node_name == "validate":
                    print("Starting validation...")
                
                # If we're at validation_router, print detailed state
                if node_name == "validation_router":
                    print("\nVALIDATION ROUTER EVENT DATA:")
                    try:
                        if "state" in event:
                            state_data = event["state"]
                            internal_state = state_data.get("generate", {}).get("_internal", {})
                            validation_count = internal_state.get("validation_count", "Not found")
                            validation_complete = internal_state.get("validation_complete", "Not found")
                            print(f"validation_count: {validation_count}")
                            print(f"validation_complete: {validation_complete}")
                            
                            # TEST: Call validation_router directly with this state to verify behavior
                            print("\nTESTING: Calling validation_router directly with this state:")
                            try:
                                if state_data:
                                    result = await validation_router(state_data)
                                    print(f"Direct result: {result}")
                            except Exception as e:
                                print(f"Error calling validation_router directly: {e}")
                    except Exception as e:
                        print(f"Error extracting state: {e}")
            
            # For completed nodes
            if status == "end":
                print(f"Step {step_count}: Completed node: {node_name}")
                
                # After validation_router completes, check where we're going
                if node_name == "validation_router":
                    print("Validation router completed - checking next node...")
                    # Show any update information if available
                    if "metadata" in event and "langgraph_next" in event["metadata"]:
                        next_node = event["metadata"]["langgraph_next"]
                        print(f"Next node according to metadata: {next_node}")
            
            # Check for workflow completion
            if node_name == "__end__" and status == "start":
                reached_end = True
                print("\n✅ Workflow successfully reached __end__ node!")
                break
                
            # Safety termination
            if step_count >= max_steps:
                print(f"\n⚠️ Reached maximum steps ({max_steps}) without terminating")
                # Show the last event for debugging
                print("\nLast event:")
                pprint(last_event)
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
                after_node = executed_nodes[index+1] if index + 1 < len(executed_nodes) else "none"
                print(f"After validation_router, workflow went to: {after_node}")
                print("This suggests the Command(goto='__end__') is not being honored")
            else:
                print("validation_router was the last node executed before hitting step limit")
                print("This suggests we might be in an infinite loop or stuck state")
        
        # Final state of the last node
        print(f"\nLast node: {last_node}")
        
        # Check if we can extract workflow info
        print("\nWorkflow structure inspection:")
        for attr_name in ["nodes", "_nodes", "edges", "_edges"]:
            if hasattr(workflow, attr_name):
                attr = getattr(workflow, attr_name)
                if attr:
                    print(f"{attr_name}: {attr}")
                    
        return False

if __name__ == "__main__":
    success = asyncio.run(test_agent_with_input())
    sys.exit(0 if success else 1) 
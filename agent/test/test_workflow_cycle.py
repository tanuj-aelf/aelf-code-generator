#!/usr/bin/env python
"""Test script to verify the agent workflow properly terminates after validation."""

import asyncio
import time
from aelf_code_generator.agent import create_agent, get_default_state

async def test_complete_workflow_cycle():
    """
    Test that the agent workflow correctly executes a full cycle and terminates after validation.
    This test simulates a real input and follows through the entire workflow,
    verifying the validation_router sends to __end__ after validation.
    """
    print("\n=== Testing complete agent workflow cycle ===\n")
    
    try:
        # Create the agent workflow
        print("Creating agent workflow...")
        workflow = create_agent()
        print("✅ Agent workflow created successfully!")
        
        # Create a minimal state with a simple input
        print("\nPreparing initial state...")
        state = get_default_state()
        state["input"] = "Create a simple token contract for AELF"
        print(f"Input: {state['input']}")
        
        print("\nExecuting the workflow...")
        print("(This will follow the execution through all nodes)")
        print("-----------------------------------------")
        
        # We'll track nodes that are executed to verify flow
        executed_nodes = []
        termination_reason = None
        
        # Execute the workflow and track the path
        async for event in workflow.astream_events(state, stream_mode="node", version="v1"):
            # In v1, the event format is different
            node_name = event.get("node")
            status = event.get("status", "unknown")
            
            if status == "start":
                executed_nodes.append(node_name)
                print(f"Executing node: {node_name}")
            
            # Check for completion
            if node_name == "__end__" and status == "start":
                termination_reason = "Workflow reached __end__ node"
                print(f"✅ {termination_reason}")
                break
        
        # Verify the correct path was taken
        print("\n-----------------------------------------")
        print("Workflow execution completed!")
        print(f"Executed nodes: {' -> '.join(executed_nodes)}")
        
        # Verify that validation_router was reached and properly terminated
        if "validation_router" in executed_nodes and executed_nodes[-1] == "__end__":
            print("✅ PASS: Workflow correctly terminated after validation_router")
        else:
            print("❌ FAIL: Workflow did not terminate correctly after validation_router")
        
        print("\nTest complete!")
    
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_complete_workflow_cycle()) 
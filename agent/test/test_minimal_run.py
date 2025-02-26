#!/usr/bin/env python
"""Test script to run a minimal agent workflow."""

import asyncio
from aelf_code_generator.agent import get_default_state, create_agent

async def run_minimal_agent():
    """Run the agent with a minimal input to test workflow execution."""
    print("\n=== Running minimal agent test ===\n")
    
    try:
        # Create a minimal starting state
        state = get_default_state()
        state["input"] = "Create a simple Hello World contract for AELF"
        
        # Create the agent workflow
        workflow = create_agent()
        print("✅ Agent workflow created successfully!")
        
        # Run the workflow for one step
        print(f"\nExecuting workflow with input: {state['input']}")
        
        # Execute workflow for a few steps to verify it runs properly
        count = 0
        async for event_info in workflow.astream_events(state, stream_mode="node", version="v1"):
            count += 1
            node_name = event_info[0].get("node")
            status = event_info[0].get("status")
            print(f"Node: {node_name}, Status: {status}")
            
            # Break after successfully running a few nodes
            if count >= 3:
                break
        
        print("\n✅ Agent workflow successfully executed multiple steps without InvalidUpdateError!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(run_minimal_agent()) 
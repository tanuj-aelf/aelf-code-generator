"""
This module provides a demo interface for the AELF smart contract code generator.
"""

import os
from dotenv import load_dotenv
load_dotenv()  # This loads the environment variables from .env

from fastapi import FastAPI, Body, HTTPException
import uvicorn
from aelf_code_generator.agent import graph, get_default_state

app = FastAPI()

@app.post("/generate")
async def generate_contract(description: str = Body(..., description="Describe your smart contract requirements in plain text. For example:\n- I need a voting contract where users can create proposals and vote\n- Create an NFT marketplace with listing and bidding features\n- Token contract with mint, burn, and transfer functions\n- DAO governance contract with proposal voting and treasury management")):
    """Generate smart contract from text description."""
    try:
        # Create initial state with description
        state = get_default_state()
        state["input"] = description
        
        # Run the graph
        result = await graph.ainvoke(state)
        
        # Check for errors
        if not any(result["output"].values()):
            raise HTTPException(
                status_code=500,
                detail="Failed to generate contract. Please try again with a more detailed description."
            )
        
        # Return the generated outputs
        return result["output"]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/health")
def health():
    """Health check."""
    return {"status": "ok"}

def main():
    """Run the uvicorn server."""
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "aelf_code_generator.demo:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        reload_dirs=["."]
    )

if __name__ == "__main__":
    main() 
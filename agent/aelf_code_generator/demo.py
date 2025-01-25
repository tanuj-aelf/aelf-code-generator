"""
This module provides a demo interface for the AELF smart contract code generator.
"""

import os
from dotenv import load_dotenv
load_dotenv()  # This loads the environment variables from .env

from fastapi import FastAPI, Body
import uvicorn
from langchain_core.messages import HumanMessage
from aelf_code_generator.agent import graph

app = FastAPI()

# Add direct text input endpoint
@app.post("/generate")
async def generate_contract(description: str = Body(..., description="Describe your smart contract requirements in plain text. For example:\n- I need a voting contract where users can create proposals and vote\n- Create an NFT marketplace with listing and bidding features\n- Token contract with mint, burn, and transfer functions\n- DAO governance contract with proposal voting and treasury management")):
    """Generate smart contract from text description."""
    # Create initial state with the human message
    state = {
        "messages": [HumanMessage(content=description)]
    }
    
    # Run the graph
    result = await graph.ainvoke(state)
    return result

# Add health check route
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
"""
Demo module for running the AELF smart contract generator agent.
"""

import os
from dotenv import load_dotenv
load_dotenv()  # This loads the environment variables from .env

from fastapi import FastAPI, Body
import uvicorn
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from copilotkit import CopilotKitSDK, LangGraphAgent
from aelf_code_generator.agent import graph

app = FastAPI()
sdk = CopilotKitSDK(
    agents=[
        LangGraphAgent(
            name="aelf_code_generator",
            description="AELF smart contract code generator agent. Provide a plain text description of your dApp and I will generate a complete smart contract.",
            graph=graph,
        )
    ],
)

add_fastapi_endpoint(app, sdk, "/copilotkit")

# Add direct text input endpoint
@app.post("/generate")
async def generate_contract(description: str = Body(..., description="Plain text description of your dApp")):
    """Generate smart contract from text description."""
    result = await graph.ainvoke(description)
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
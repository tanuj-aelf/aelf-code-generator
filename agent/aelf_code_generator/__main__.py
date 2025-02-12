"""Main entry point for the AELF code generator agent."""

import os
import json
import uvicorn
import logging
from typing import Dict, Any, List
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from copilotkit import CopilotKitSDK, LangGraphAgent
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from aelf_code_generator.agent import create_agent, graph

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for the FastAPI application."""
    # Initialize on startup
    logger.info("Starting up the application...")
    yield
    # Cleanup on shutdown
    logger.info("Shutting down the application...")

app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize CopilotKit SDK with our agent
sdk = CopilotKitSDK(
    agents=[
        LangGraphAgent(
            name="aelf_code_generator",
            description="Generates AELF smart contract code based on natural language descriptions.",
            graph=graph,
        )
    ],
)

# Custom message handler
async def handle_messages(messages: List[Dict[str, str]]) -> JSONResponse:
    """Handle incoming messages and return a JSON response."""
    try:
        # Log incoming messages
        logger.info(f"Received messages: {messages}")
        
        # Create initial state
        state = {
            "input": messages[-1]["content"] if messages else "",
            "messages": messages
        }
        
        # Accumulate all events
        events = []
        try:
            async for event in graph.astream(state):
                logger.info(f"Generated event: {event}")
                events.append(event)
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": str(e)}
            )
        
        # Return the last event as the final response
        if events:
            last_event = events[-1]
            # Extract the internal output from the last event
            if "_internal" in last_event.get("analyze", {}):
                internal_output = last_event["analyze"]["_internal"]["output"]
                # Format response for frontend
                response = {
                    "analyze": {
                        "contract": internal_output.get("contract", {}).get("content", ""),
                        "proto": internal_output.get("proto", {}).get("content", ""),
                        "state": internal_output.get("state", {}).get("content", ""),
                        "project": internal_output.get("project", {}).get("content", ""),
                        "reference": internal_output.get("reference", {}).get("content", ""),
                        "analysis": internal_output.get("analysis", ""),
                        "metadata": internal_output.get("metadata", [])
                    }
                }
                return JSONResponse(content=response)
            else:
                # Fallback if output structure is different
                return JSONResponse(content=last_event)
        else:
            return JSONResponse(
                status_code=500,
                content={"error": "No response generated"}
            )
    except Exception as e:
        logger.error(f"Error in handle_messages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Add custom endpoint handlers
@app.post("/copilotkit")
@app.post("/copilotkit/generate")
async def copilotkit_endpoint(request: Request):
    """Handle requests to the copilotkit endpoint."""
    try:
        body = await request.json()
        messages = body.get("messages", [])
        return await handle_messages(messages)
    except Exception as e:
        logger.error(f"Error in copilotkit_endpoint: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to process request: {str(e)}"}
        )

# Health check endpoint
@app.get("/health")
def health():
    """Health check."""
    return {"status": "ok"}

def main():
    """Start the FastAPI server."""
    load_dotenv()
    
    # Start the server
    logger.info("Starting the FastAPI server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=3001,
        log_level="info"
    )

if __name__ == "__main__":
    main() 
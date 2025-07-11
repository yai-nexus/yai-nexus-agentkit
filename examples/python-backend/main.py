#!/usr/bin/env python3
"""
Simple Python backend example for yai-nexus-fekit SDK
This is a minimal echo server that demonstrates the ag-ui-protocol integration
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json
import time
import asyncio
from typing import Dict, Any, AsyncGenerator
from pydantic import BaseModel

app = FastAPI(
    title="YAI Nexus FeKit Python Backend",
    description="Example backend for demonstrating yai-nexus-agentkit integration",
    version="0.1.0"
)

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MessageRequest(BaseModel):
    content: str
    metadata: Dict[str, Any] = {}

class AgUiEvent(BaseModel):
    type: str
    data: Dict[str, Any]

@app.get("/")
async def root():
    return {
        "message": "YAI Nexus FeKit Python Backend",
        "version": "0.1.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

async def generate_streaming_response(content: str) -> AsyncGenerator[str, None]:
    """
    Generate a streaming response that simulates an AI agent
    responding with ag-ui-protocol events
    """
    
    # Start event
    start_event = AgUiEvent(
        type="start",
        data={"message_id": f"msg_{int(time.time())}"}
    )
    yield f"data: {start_event.model_dump_json()}\n\n"
    
    # Simulate thinking delay
    await asyncio.sleep(0.5)
    
    # Simulate streaming text response
    response_text = f"Echo: {content}\n\nThis is a demonstration of the yai-nexus-fekit SDK. Your message was received and processed by the Python backend using ag-ui-protocol."
    
    words = response_text.split()
    for i, word in enumerate(words):
        # Text chunk event
        chunk_event = AgUiEvent(
            type="text_chunk",
            data={
                "text": word + " ",
                "index": i,
                "total": len(words)
            }
        )
        yield f"data: {chunk_event.model_dump_json()}\n\n"
        
        # Small delay between words for realistic streaming effect
        await asyncio.sleep(0.1)
    
    # Tool call demonstration (optional)
    if "tool" in content.lower() or "function" in content.lower():
        tool_call_event = AgUiEvent(
            type="tool_call",
            data={
                "name": "echo_tool",
                "arguments": {"input": content}
            }
        )
        yield f"data: {tool_call_event.model_dump_json()}\n\n"
        
        await asyncio.sleep(0.3)
        
        tool_result_event = AgUiEvent(
            type="tool_result",
            data={
                "result": f"Tool executed successfully with input: {content}"
            }
        )
        yield f"data: {tool_result_event.model_dump_json()}\n\n"
    
    # End event
    end_event = AgUiEvent(
        type="end",
        data={
            "status": "completed",
            "token_count": len(words),
            "processing_time": len(words) * 0.1 + 0.5
        }
    )
    yield f"data: {end_event.model_dump_json()}\n\n"

@app.post("/invoke")
async def invoke_agent(request: MessageRequest):
    """
    Main endpoint that receives messages from the frontend
    and returns streaming ag-ui-protocol responses
    """
    try:
        content = request.content.strip()
        
        if not content:
            raise HTTPException(status_code=400, detail="Message content cannot be empty")
        
        print(f"Received message: {content}")
        print(f"Metadata: {request.metadata}")
        
        # Return streaming response
        return StreamingResponse(
            generate_streaming_response(content),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )
        
    except Exception as e:
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test")
async def test_endpoint(request: MessageRequest):
    """
    Simple test endpoint that returns a non-streaming response
    """
    return {
        "echo": request.content,
        "metadata": request.metadata,
        "timestamp": time.time(),
        "message": "This is a test response from the Python backend"
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting YAI Nexus FeKit Python Backend...")
    print("Backend will be available at: http://127.0.0.1:8000")
    print("API documentation at: http://127.0.0.1:8000/docs")
    
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
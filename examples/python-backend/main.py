#!/usr/bin/env python3
"""
Simple Python backend example for yai-nexus-fekit SDK
This is a minimal echo server that demonstrates the ag-ui-protocol integration
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json
import time
import asyncio
from typing import Dict, Any, AsyncGenerator, List, Optional
import uuid
from pydantic import BaseModel

# 核心依赖 - 从 ag-ui 导入标准事件和请求模型
from ag_ui.core import RunAgentInput
from ag_ui.core.events import (
    EventType,
    RunStartedEvent,
    TextMessageChunkEvent,
    ToolCallStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    ToolCallResultEvent,
    RunFinishedEvent,
)

# We will use print for logging for now to ensure visibility with uvicorn

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

# --- This is no longer needed, we use RunAgentInput from the library ---
# class ChatMessage(BaseModel):
#     """Represents a single message in the chat history."""
#     role: str
#     content: str

# class ChatRequest(BaseModel):
#     """
#     Represents the request body sent by the fekit client.
#     Based on common AG-UI patterns.
#     """
#     messages: List[ChatMessage]
#     threadId: Optional[str] = None
#     runId: Optional[str] = None
#     properties: Optional[Dict[str, Any]] = None


# --- This is no longer needed, we use RunAgentInput from the library ---
# class MessageRequest(BaseModel):
#     content: str
#     metadata: Dict[str, Any] = {}

# class AgUiEvent(BaseModel):
#     type: str
#     data: Dict[str, Any]

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

async def generate_streaming_response(content: str, run_id: str, thread_id: str) -> AsyncGenerator[str, None]:
    """
    (Restored) Generate a streaming response that simulates an AI agent
    responding with ag-ui-protocol events, using official event models.
    """
    print(f"Generating full response for content: '{content}'")
    
    # Start event
    start_event = RunStartedEvent(
        type=EventType.RUN_STARTED,
        run_id=run_id,
        thread_id=thread_id
    )
    yield f"data: {start_event.model_dump_json()}\n\n"
    await asyncio.sleep(0.5)
    
    # Simulate streaming text response
    response_text = f"Echo: {content}\n\nThis is a demonstration using ag_ui.core.events. Your message was received and processed."
    words = response_text.split()
    for i, word in enumerate(words):
        chunk_event = TextMessageChunkEvent(
            type=EventType.TEXT_MESSAGE_CHUNK,
            delta=word + " "
        )
        yield f"data: {chunk_event.model_dump_json()}\n\n"
        await asyncio.sleep(0.1)
    
    # Tool call demonstration
    if "tool" in content.lower() or "function" in content.lower():
        tool_call_id = f"tool_call_{uuid.uuid4().hex}"
        # ... (rest of tool call logic from before)
        tool_call_event = ToolCallStartEvent(
            type=EventType.TOOL_CALL_START,
            tool_call_id=tool_call_id,
            tool_call_name="echo_tool"
        )
        yield f"data: {tool_call_event.model_dump_json()}\n\n"
        await asyncio.sleep(0.1)

        args_event = ToolCallArgsEvent(
            type=EventType.TOOL_CALL_ARGS,
            tool_call_id=tool_call_id,
            delta=json.dumps({"input": content})
        )
        yield f"data: {args_event.model_dump_json()}\n\n"
        await asyncio.sleep(0.3)
        
        end_event = ToolCallEndEvent(
             type=EventType.TOOL_CALL_END,
             tool_call_id=tool_call_id
        )
        yield f"data: {end_event.model_dump_json()}\n\n"
        await asyncio.sleep(0.1)

        result_event = ToolCallResultEvent(
            type=EventType.TOOL_CALL_RESULT,
            tool_call_id=tool_call_id,
            message_id=tool_call_id, # Simplified for example
            content=f"Tool executed successfully with input: {content}"
        )
        yield f"data: {result_event.model_dump_json()}\n\n"

    # End event
    end_event = RunFinishedEvent(
        type=EventType.RUN_FINISHED,
        run_id=run_id,
        thread_id=thread_id,
    )
    yield f"data: {end_event.model_dump_json()}\n\n"
    print(f"Finished generating full response for run_id: {run_id}")


@app.post("/invoke")
async def invoke_agent(request: RunAgentInput):
    """
    Main endpoint that receives AG-UI standard RunAgentInput
    and returns streaming ag-ui-protocol responses.
    """
    try:
        print(f"Received request: {request.model_dump_json(indent=2)}")

        if not request.messages:
            raise HTTPException(status_code=400, detail="Request body must contain 'messages' array.")

        last_message = request.messages[-1]
        content = last_message.content.strip()

        if not content:
            raise HTTPException(status_code=400, detail="The last message must have non-empty 'content'.")

        print(f"Extracted content: {content}")
        
        # Use IDs from the request, or generate new ones
        run_id = request.run_id or f"run_{uuid.uuid4().hex}"
        thread_id = request.thread_id or f"thread_{uuid.uuid4().hex}"

        return StreamingResponse(
            generate_streaming_response(content, run_id=run_id, thread_id=thread_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )
        
    except Exception as e:
        print(f"Error processing request: {e}")
        # Also log the full exception for debugging
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



# --- The old /test endpoint, kept for simple checks ---
class MessageRequest(BaseModel):
    content: str
    metadata: Dict[str, Any] = {}

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
        log_level="info"  # Restore uvicorn's logger
    )
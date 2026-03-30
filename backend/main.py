"""
Xiaozhi Digital Assistant - FastAPI Backend
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import logging

from config import settings
from llm_wrapper import get_llm

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Xiaozhi Digital Assistant API",
    description="AI Digital Assistant powered by Tongyi LLM",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    conversation_id: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    conversation_id: str
    tokens_used: Optional[int] = None


# Health Check Endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Xiaozhi Digital Assistant API",
        "version": "0.1.0"
    }


# Chat Endpoint
@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Chat endpoint for sending messages to the LLM
    """
    if not request.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    try:
        logger.info(f"Processing chat request: {request.message}")
        
        # Get LLM instance
        try:
            llm = get_llm()
        except ValueError as e:
            error_msg = f"LLM initialization failed: {str(e)}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Call LLM with user message
        try:
            response = llm.chat(request.message)
            logger.info(f"Generated response: {response[:100] if response else 'No response'}...")
        except Exception as llm_error:
            error_msg = f"LLM call failed: {str(llm_error)}"
            logger.error(error_msg, exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)
        
        return ChatResponse(
            response=response,
            conversation_id=request.conversation_id or "default"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/", tags=["Info"])
async def root():
    """Root endpoint"""
    return {
        "message": "Xiaozhi Digital Assistant API",
        "docs": "/docs"
    }


# Streaming Chat Endpoint
@app.post("/chat/stream", tags=["Chat"])
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint - returns response as stream
    Uses Server-Sent Events (SSE) format
    """
    if not request.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    async def event_generator():
        """Generate streaming events"""
        import json
        try:
            logger.info(f"Processing streaming chat request: {request.message}")
            
            # Get LLM instance
            try:
                llm = get_llm()
            except ValueError as e:
                error_msg = f"LLM initialization failed: {str(e)}"
                logger.error(error_msg)
                yield f'data: {json.dumps({"error": error_msg})}\n\n'
                return
            
            # Stream the response
            try:
                full_response = ""
                
                for chunk in llm.chat_stream(request.message):
                    if chunk:
                        full_response += chunk
                        # Send chunk as SSE data (json.dumps handles all escaping)
                        yield f'data: {json.dumps({"chunk": chunk})}\n\n'
                
                # Send completion message
                yield f'data: {json.dumps({"done": True, "total": full_response})}\n\n'
                logger.info(f"Streaming completed. Length: {len(full_response)}")
                
            except Exception as llm_error:
                error_msg = f"LLM call failed: {str(llm_error)}"
                logger.error(error_msg, exc_info=True)
                yield f'data: {json.dumps({"error": error_msg})}\n\n'
                
        except Exception as e:
            logger.error(f"Error in streaming: {str(e)}", exc_info=True)
            yield f'data: {json.dumps({"error": str(e)})}\n\n'
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )

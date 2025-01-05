"""Chat Interface
====================
A minimal chat interface implementation using FastAPI and WebSocket.

Design Decisions:
- Uses WebSocket-based session management for chat history
- Implements Gemini API integration through custom wrapper
- Uses WebSocket for real-time communication
- Templated HTML/CSS frontend for chat interface
- Maintains conversation context per WebSocket connection
- Includes real-time cost tracking and display

Integration Notes:
- Requires GEMINI_API_KEY in environment variables
- Runs on default port 8000
- Static files served from /static directory
- Templates stored in /templates directory
- Uses CostTracker for budget management
"""

import os
import sys
import json
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uuid

from app.llms.gemini import gemini_api
from utils.logging_config import get_logger

# Get logger instance
logger = get_logger(__name__)

# Check for required environment variables early
if not os.getenv("GEMINI_API_KEY"):
    logger.error("GEMINI_API_KEY environment variable not set!")
    sys.exit(1)

# Create FastAPI application
app = FastAPI(title="Gemini Chat Interface")

# Mount static files directory
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

# Configure templates
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

@app.get("/")
async def get(request: Request):
    """Serve the chat interface."""
    return templates.TemplateResponse("chat.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections for chat."""
    await websocket.accept()
    
    # Create a unique session ID for this connection
    session_id = str(uuid.uuid4())
    logger.info(f"New chat session started: {session_id}")
    
    try:
        while True:
            message = await websocket.receive_text()
            logger.info(f"Received message: {message[:50]}...")
            
            try:
                # Generate response
                response = await gemini_api.generate_content(message, session_id)
                
                # Get cost information
                cost_info = {
                    "request_cost": gemini_api.cost_tracker.get_session_costs(session_id).last_request_cost,
                    "total_cost": gemini_api.cost_tracker.get_total_cost(session_id),
                    "remaining_budget": gemini_api.cost_tracker.get_remaining_budget(session_id)
                }
                
                # Send response with cost information
                await websocket.send_json({
                    "message": response,
                    "cost_info": cost_info
                })
                
                logger.info(
                    f"Sent response successfully. "
                    f"Cost: ${cost_info['request_cost']:.3f}, "
                    f"Total: ${cost_info['total_cost']:.3f}"
                )
            except ValueError as e:
                # Budget exceeded
                error_message = str(e)
                await websocket.send_json({
                    "message": f"Error: {error_message}",
                    "cost_info": {
                        "total_cost": gemini_api.cost_tracker.get_total_cost(session_id),
                        "remaining_budget": gemini_api.cost_tracker.get_remaining_budget(session_id)
                    }
                })
                logger.error(error_message)
            except Exception as e:
                error_message = f"Error generating response: {str(e)}"
                await websocket.send_json({
                    "message": "Sorry, I encountered an error processing your request."
                })
                logger.error(error_message)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")

# Only run server directly when script is executed directly
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting chat server...")
    uvicorn.run(
        "app.ui.chat_ui:app",  # Fixed import path
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(Path(__file__).parent.parent.parent)]  # Monitor root directory for changes
    ) 
"""Chat Interface
====================
A minimal chat interface implementation using FastAPI and WebSocket.

Design Decisions:
- Uses WebSocket-based session management for chat history
- Implements Gemini API integration through custom wrapper
- Uses WebSocket for real-time communication
- Templated HTML/CSS frontend for chat interface
- Maintains conversation context per WebSocket connection

Integration Notes:
- Requires GEMINI_API_KEY in environment variables
- Runs on default port 8000
- Static files served from /static directory
- Templates stored in /templates directory
"""

import os
import sys
from pathlib import Path
import uuid

# Add parent directory to Python path for imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
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
                response = await gemini_api.generate_content(message, session_id)
                await websocket.send_text(response)
                logger.info("Sent response successfully")
            except Exception as e:
                error_message = f"Error generating response: {str(e)}"
                logger.error(error_message)
                await websocket.send_text("Sorry, I encountered an error processing your request.")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")

# Only run server directly when script is executed directly
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting chat server...")
    uvicorn.run(
        "chat_ui:app",  # Use import string format
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[parent_dir]  # Monitor parent directory for changes
    ) 
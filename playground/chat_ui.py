"""Chat Interface
====================
A minimal chat interface implementation using FastAPI and WebSocket.

Design Decisions:
- Uses WebSocket-based session management for chat history
- Implements Gemini API integration through custom wrapper
- Uses WebSocket for real-time communication
- Simple HTML/JS frontend for chat interface
- Maintains conversation context per WebSocket connection

Integration Notes:
- Requires GEMINI_API_KEY in environment variables
- Runs on default port 8000
"""

import os
import sys
from pathlib import Path
import uuid

# Add parent directory to Python path for imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import logging
from app.llms.gemini import gemini_api

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='\033[92m%(asctime)s\033[0m \033[94m%(levelname)s\033[0m: %(message)s'
)
logger = logging.getLogger(__name__)

# Check for required environment variables early
if not os.getenv("GEMINI_API_KEY"):
    logger.error("\033[91mGEMINI_API_KEY environment variable not set!\033[0m")
    sys.exit(1)

# Create FastAPI application
app = FastAPI(title="Gemini Chat Interface")

# Simple in-memory message history
chat_history = []

# HTML template for the chat interface
HTML = """
<!DOCTYPE html>
<html>
    <head>
        <title>Gemini Chat Interface</title>
        <style>
            body { 
                max-width: 800px; 
                margin: 0 auto; 
                padding: 20px;
                font-family: Arial, sans-serif;
            }
            #messages { 
                height: 400px; 
                overflow-y: auto; 
                border: 1px solid #ddd; 
                padding: 20px;
                margin-bottom: 20px;
                border-radius: 5px;
            }
            #messageInput { 
                width: 80%; 
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            button { 
                padding: 10px 20px;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            button:hover { background: #0056b3; }
            .message { margin: 10px 0; }
            .user { color: #007bff; }
            .bot { color: #28a745; }
        </style>
    </head>
    <body>
        <h1>Gemini Chat Interface</h1>
        <div id="messages"></div>
        <input type="text" id="messageInput" placeholder="Type your message...">
        <button onclick="sendMessage()">Send</button>
        <script>
            var ws = new WebSocket("ws://" + window.location.host + "/ws");
            
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages');
                var message = document.createElement('div');
                message.className = 'message bot';
                message.innerHTML = '<strong>Bot:</strong> ' + event.data;
                messages.appendChild(message);
                messages.scrollTop = messages.scrollHeight;
            };
            
            function sendMessage() {
                var input = document.getElementById("messageInput");
                if (input.value) {
                    var messages = document.getElementById('messages');
                    var message = document.createElement('div');
                    message.className = 'message user';
                    message.innerHTML = '<strong>You:</strong> ' + input.value;
                    messages.appendChild(message);
                    
                    ws.send(input.value);
                    input.value = '';
                    messages.scrollTop = messages.scrollHeight;
                }
            }
            
            // Allow sending message with Enter key
            document.getElementById("messageInput").addEventListener("keypress", function(e) {
                if (e.key === "Enter") {
                    sendMessage();
                }
            });
        </script>
    </body>
</html>
"""

@app.get("/")
async def get():
    """Serve the chat interface."""
    return HTMLResponse(HTML)

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
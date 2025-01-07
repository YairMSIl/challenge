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
- Supports image generation with Eden AI
- Uses base64 for direct image display
- Saves debug images to logs/images directory

Integration Notes:
- Requires GEMINI_API_KEY and EDEN_API_KEY in environment variables
- Runs on default port 8000
- Static files served from /static directory
- Templates stored in /templates directory
- Uses CostTracker for budget management
- Debug images stored in logs/images directory
"""

import os
import sys
import json
from pathlib import Path

from app.image_generators.eden import EdenImageGenerator
from app.models.artifact import ArtifactType

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uuid

from app.agent_framework.agents.gemini_agent import GeminiAgent
from utils.logging_config import get_logger

# Get logger instance
logger = get_logger(__name__)

# Check for required environment variables early
if not os.getenv("GEMINI_API_KEY"):
    logger.error("GEMINI_API_KEY environment variable not set!")
    sys.exit(1)
if not os.getenv("EDEN_API_KEY"):
    logger.error("EDEN_API_KEY environment variable not set!")
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
    session_id = str(uuid.uuid4()).replace('-', '')[:32]  # Remove hyphens and limit to 32 chars
    logger.info(f"New chat session started: {session_id}")
    
    # Initialize agents once per session
    eden_image_generator = EdenImageGenerator()
    gemini_agent_api = GeminiAgent(session_id=session_id)
    
    try:
        while True:
            message = await websocket.receive_text()
            logger.info(f"Received message: {message[:50]}...")
            
            try:
                # Check if this is an image generation request
                is_image_request = message.lower().startswith(("/image"))
                
                if is_image_request:
                    # Generate image
                    result = eden_image_generator.generate_image(message, session_id)
                    
                    # Check for errors
                    if result.get("error", False):
                        error_message = result.get("message", "Unknown error occurred during image generation")
                        
                        # Try to get cost info, use None if not available
                        try:
                            cost_info = {
                                "request_cost": eden_image_generator.cost_tracker.get_session_costs(session_id).last_request_cost,
                                "total_cost": eden_image_generator.cost_tracker.get_total_cost(session_id),
                                "remaining_budget": eden_image_generator.cost_tracker.get_remaining_budget(session_id)
                            }
                        except (AttributeError, Exception) as e:
                            logger.debug(f"Could not get cost info during error: {str(e)}")
                            cost_info = None
                            
                        await websocket.send_json({
                            "message": f"Error: {error_message}",
                            "cost_info": cost_info
                        })
                        continue
                    
                    # Get cost information for successful requests
                    cost_info = {
                        "request_cost": eden_image_generator.cost_tracker.get_session_costs(session_id).last_request_cost,
                        "total_cost": eden_image_generator.cost_tracker.get_total_cost(session_id),
                        "remaining_budget": eden_image_generator.cost_tracker.get_remaining_budget(session_id)
                    }
                    
                    # Send response with base64 image and cost information
                    await websocket.send_json({
                        "message": "Here's your generated image:",
                        "base64_image": result["base64_image"],
                        "cost_info": cost_info
                    })
                    
                    logger.info(
                        f"Image generated successfully. "
                        f"Cost: ${cost_info['request_cost']:.3f}, "
                        f"Total: ${cost_info['total_cost']:.3f}"
                    )
                else:
                    # Generate text response
                    response = await gemini_agent_api.generate_content(message)
                    # TODO: Use the below snippet to extract tool_calls for the UI
                    # for i, log in enumerate(gemini_agent_api.get_or_create_agent(session_id).logs):
                    #     logger.warning(f"Log {i}: {log}")
                    
                    # Get cost information
                    cost_info = {
                        "request_cost": gemini_agent_api.cost_tracker.get_session_costs(session_id).last_request_cost,
                        "total_cost": gemini_agent_api.cost_tracker.get_total_cost(session_id),
                        "remaining_budget": gemini_agent_api.cost_tracker.get_remaining_budget(session_id)
                    }
                    
                    # Get agent flow for debugging/monitoring
                    agent_flow = gemini_agent_api.get_agent_flow(session_id)
                    
                    # Send response with cost information and agent flow
                    ok_response_json = {
                        "message": response,
                        "cost_info": cost_info,
                        "agent_flow": agent_flow  # This will be available for debugging/monitoring
                    }

                    # Check if we have artifacts to display
                    for artifact in gemini_agent_api.session_artifacts[session_id]:
                        if not artifact.is_new:
                            continue

                        if artifact.type == ArtifactType.IMAGE.value:
                            ok_response_json["base64_image"] = artifact.content
                            artifact.is_new = False
                        
                        if artifact.type == ArtifactType.AUDIO.value:
                            ok_response_json["base64_audio"] = artifact.content
                            artifact.is_new = False

                        if artifact.type == ArtifactType.RESEARCH.value:
                            ok_response_json["research_result"] = artifact.content
                            artifact.is_new = False

                    await websocket.send_json(ok_response_json)
                    
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
                        "total_cost": gemini_agent_api.cost_tracker.get_total_cost(session_id),
                        "remaining_budget": gemini_agent_api.cost_tracker.get_remaining_budget(session_id)
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
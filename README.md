# AI-Powered Chat Interface

A sophisticated chat interface that combines multiple AI capabilities including text generation, image generation, audio generation, and research capabilities. The application uses Google's Gemini API as its core language model, with additional integrations for specialized tasks.

## Features

- 🤖 Advanced chat interface with Gemini AI
- 🎨 Image generation support via Eden AI
- 🔊 Audio generation capabilities
- 🔍 Integrated research tools with Google Search
- 💰 Real-time cost tracking and budget management
- 📊 Debug logging and monitoring
- ⚡ WebSocket-based real-time communication
- 🎯 Session-based conversation management

## Prerequisites

- Python 3.8 or higher
- Required API keys:
  - Google Gemini API key
  - Eden AI API key
  - Google Search API key and CSE ID for research capabilities
  - AIML API key for additional features

## Installation

1. Extract the ZIP file to your desired location

2. Create and activate a virtual environment:
```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On Unix or MacOS
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Fill in your API keys and configuration:
```env
GEMINI_API_KEY=your_gemini_api_key_here
EDEN_API_KEY=your_eden_api_key_here
AIML_API_KEY=your_aiml_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_CSE_ID=your_google_cse_id_here

# Environment Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO

# Mock Settings
USE_IMAGE_MOCK_IF_AVAILABLE=False
USE_AUDIO_MOCK_IF_AVAILABLE=False
USE_SEARCH_MOCK_IF_AVAILABLE=False
```

## Running the Application

1. Start the chat interface:
```bash
python -m app.ui.chat_ui
```

2. Open your browser and navigate to:
```
http://localhost:8000
```

## Usage Examples

1. **Text Generation**
   - Simply type your message and press enter
   - The AI will respond with relevant information (Basic AI chat - does not require any tools)

2. **Image Generation**
   - Start your message with `/image` (Example of directly invoking the image generation tool)
   - Example: `/image create a beautiful sunset over mountains`
   - Generally ask the model to generate an image with a specific style or theme.

3. **Research Queries**
   - The AI will automatically use research tools when needed
   - Ask questions that require current information or fact-checking or directly request a research/report.

4. **Audio Generation**
   - ask the model to generate audio or a song with a specific style

## Development Notes

- The application uses WebSocket for real-time communication
- Debug logs are stored in the `logs/` directory
- Generated images and audio tracks are saved in `logs/images/` and `logs/audio/` directories
- Mock services are available for testing without API keys

## Project Structure

```
.
├── app/
│   ├── agent_framework/    # Core agent implementation
│   ├── audio_generators/   # Audio generation services
│   ├── image_generators/   # Image generation services
│   ├── models/            # Data models
│   └── ui/                # Web interface
├── design/                # Design documents
├── mock/                  # Mock services
├── utils/                 # Helper utilities
└── requirements.txt       # Project dependencies
```

## Technical documentation with design decisions and architecture

Decided to go with a `chat` iterface that does not directly expose the APIs via keywords (left a sample usage of keyword API invokation with `/image bla bla bla` to show how it could be done). The chat is powered by a Gemini 2.0 flash model agent that can conversationally answer user's questions and queries, as well as invoke specific tools for the API based tasks.
The agent framework is based on a new library called `smolagents` from huggingface, which provides an easy way to create and manage agents and their tools.
Since the agent cannot directly return complex objects, like images and audio tracks, I've implemented an 'artifact' mechanism that goes down to the tool level and provides essentailly a 'work around' the context of the agent. That way, we do not have to pass huge objects (base64 of an image for instance) through the contenxt window of the agent, rather directly present to the user.
The cost tracker was planned to be implemented at the lowest level of each API call, providing direct real time cost tracking for the API invocations. Each API wrapper would implement a cost callback function that would calculate the cost of the request based on the API configuration and update the session's cost tracker.

Agent hierarchy:
- Core agent (based on gemini 2.0 flash and is the main agent that handles the conversation)
- Tools (each tool implements a specific API call, like image generation, audio generation, research, etc.)
- - Image generation tool (based on eden AI)
- - Audio generation tool (based on mubert API)
- - Research tool implemented as a wrapper to a second agent
- - - Research agent (based on gemini 2.0 flash)
- - - - Google search tool (based on google search API)
Note: We are handling the research as an external API call, thus it is wrapped as a tool. The implementation is based on a second agent which provides the said hierarchy and in my opinion provides greater flexibility and control over more complex tasks like research.

Each external API is implemented separately as a module and is wrapped as a tool. This is to allow ease of introducing additional APIs or changing the existing ones. In general, we should be able to expose internal agent's communication to the user and have deeper control over the tools and their outputs. For example, asking the model to generate an image can invoke an internal agent that is solely responsible for the image generation. That agent can then query the user for details and provide a list of options to choose from.

## Future improvements

1. **User Management and Authentication**
   - Implement user authentication and session management
   - Store user interactions in a dedicated database with proper user isolation
   - Support multiple API keys per user for different services
   - Rate limiting and usage tracking per user

2. **Asynchronous Task Management** 
   - Implement async message queue for long-running tasks
   - Add task status tracking and progress updates where applicable
   - Allow task cancellation from UI
   - Provide fallback mechanisms for failed tasks

3. **API Key Management**
   - Dynamic API key injection per user/session
   - Secure storage and encryption of API keys
   - Usage tracking and quota management per key

4. **UI/UX Improvements**
   - Add loading states and progress indicators where applicable
   - Implement task cancellation UI
   - Show real-time cost estimates
   - Add concurrent task support for long running tasks (Decide how we want the UX to be when it takes long time to get a response)
   - Improve error handling and user feedback
   - What happens if a user sends more messages before we reply? Are we going to queue them up? Prevent user from sending more messages until we reply?

5. **Architecture Enhancements**
   - Move to fully async architecture
   - Improve logging and monitoring
   - Add proper error recovery mechanisms

6. **Security Improvements**
   - Add proper authentication flow
   - Implement rate limiting
   - Improve error handling
   - Implement security measures both for APIs and LLM attacks (prompt injection, etc.)

- Put the research results, in md format, as an artifact in the agent's response
- 

- cost tracker for the API to the agent (LLM) as well as any other external tool used - needs to be properly incorporated into the agent and reflect actual usage of tokens and not only user prompt and response.
- Make sure cost is captured within the agent and any sub-tool/agent calls
- agent flow section does not contain the content of the agent interactions with tools.



Bugs:
1) 


To Figure:
1) Why do we get the init flow twice? 'app.agent_framework.agents.gemini_agent - DEBUG - GeminiAPIAgent initialized successfully' happend twice
    It seems to trigger a second time when we load the UI



Considerations for the project (might not implement)
- database to save user interactions separated from other users
- authentication and unique identifiers for the users
- Async nature of messages and long running tasks (research/audio) - How to handle? Do we block the user in the UI and allow them to cancel the task?
- injecting API keys to the tools/agents dynamically, not singelton, so we can use different keys for different users
- 

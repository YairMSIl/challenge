- implement the agent logic to control the flow
- - Response from the agent in case of creating an image should better than the key of the base64 image.
- cost tracker for the API to the agent (LLM) as well as any other external tool used - needs to be properly incorporated into the agent and reflect actual usage of tokens and not only user prompt and response.
- Make sure cost is captured within the agent and any sub-tool/agent calls
- 


To Figure:
1) Why do we get the init flow twice? 'app.agent_framework.agents.gemini_agent - DEBUG - Gemini API configured successfully' happend twice
    It seems to trigger a second time when we load the UI



Considerations for the project (probably wont implement)
- database to save user interactions separated from other users
- authentication and unique identifiers for the users
- 
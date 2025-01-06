- cost tracker for the API to the agent (LLM) as well as any other external tool used - needs to be properly incorporated into the agent and reflect actual usage of tokens and not only user prompt and response.
- Make sure cost is captured within the agent and any sub-tool/agent calls
- agent flow section does not contain the content of the agent interactions with tools.
- Remove the tons of logging from the agent API calls to the LLM


Bugs:
1) Artifacts keep being presented to the UI for few messages down the road
2) 


To Figure:
1) Why do we get the init flow twice? 'app.agent_framework.agents.gemini_agent - DEBUG - Gemini API configured successfully' happend twice
    It seems to trigger a second time when we load the UI



Considerations for the project (probably wont implement)
- database to save user interactions separated from other users
- authentication and unique identifiers for the users
- 
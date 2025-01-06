- issue with cost tracker. It is showing, for global cost, the cost of a single request, the last one.
- 

- cost tracker for the API to the agent (LLM) as well as any other external tool used - needs to be properly incorporated into the agent and reflect actual usage of tokens and not only user prompt and response.
- Make sure cost is captured within the agent and any sub-tool/agent calls
- agent flow section does not contain the content of the agent interactions with tools.

- Issue where we do not see tool calls and internal 'agent' thoughts in the UI

- Updated design document
- Updated readme.md and proper description of the project and how to run it including examples
- Possible docker setup for the project for easier deployment


Tidy up the code
1) Split up code into more files
2) Consts for strings and other static values
3) Enums where applicable
4) single purpose functions (generally, not long and not too  many indentations)
5) Remove unused code and imports
6) less JSONs more objects. 


Bugs:
1) 


To Figure:
1) 



Considerations for the project (might not implement)
- database to save user interactions separated from other users
- authentication and unique identifiers for the users
- Async nature of messages and long running tasks (research/audio) - How to handle? Do we block the user in the UI and allow them to cancel the task?
- injecting API keys to the tools/agents dynamically, not singelton, so we can use different keys for different users
- 

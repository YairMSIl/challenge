- implement the agent logic to control the flow
- - Generating an image by the agent should not dump the entire base64 to the screen, rather it should provide path to a temp file where the content of the file is saved or we can use memory to do it, so send a 'key' to a dictionary with the images to be used.
- cost tracker for the API to the agent (LLM) as well as any other external tool used
- start with agent that can talk and create images only, later we add tools for the rest
- Make sure cost is captured within the agent and any sub-tool/agent calls
- 



Considerations for the project (probably wont implement)
- database to save user interactions separated from other users
- authentication and unique identifiers for the users
- 
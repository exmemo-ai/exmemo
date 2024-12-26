## 1 [1.0.2] - 2024-12-30

### 1.1 Added

* Integrated chat interface on the frontend
* Stored chat history in the database
* Added proxy functionality: User inputs starting with "/" are parsed as commands, while others are treated as chat

### 1.2 Changed

- Users can set the scope of the chat context.
- Limited the usage only to the default LLM.
- Change the setting method: users can set LLM resources themselves, including APIKey, etc. (environment variables `DEFAULT_TOOL_*` and `DEFAULT_CHAT_*` need to be adjusted accordingly during deployment, see `default_env` example for more details)
### 1.3 Fixed

- Case-insensitive document search
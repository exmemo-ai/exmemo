## 1 [1.1.0] - 2024-12-31

### 1.1 Added

- Integrated chat interface on the frontend
- Stored chat history in the database
- Added proxy functionality: User inputs starting with "/" are parsed as commands, while others are treated as chat

### 1.2 Changed

- Users can set the scope of the chat context.
- Limited the usage only to the default LLM.
- Change the setting method: users can set LLM resources themselves, including APIKey, etc. (environment variables `DEFAULT_TOOL_*` and `DEFAULT_CHAT_*` need to be adjusted accordingly during deployment, see `default_env` example for more details)
### 1.3 Fixed

- Case-insensitive document search

## 2 [1.1.1] - 2025-01-15

### 2.1 Added

- Added a data viewing interface that supports opening markdown notes, images, files, and web pages in the frontend, along with highlighting and saving capabilities.
- Translation tool now includes a learning feature, supporting functions like selecting words to learn, studying, reviewing, dictation, and summarizing.
- The frontend chat interface now allows deleting conversations, renaming conversations, and uploading files.

### 2.2 Changed

- Files now use their filenames as titles.
- Modified conversation synchronization logic.
- Adjusted data management in the frontend: updated the upload and edit dialog boxes and the list layout.

### 2.3 Fixed

- Fixed incorrect chat timestamps.


## 3 [1.1.2] - 2025-01-20

### 3.1 Added

- Integrated bookmark management UI with navigation, search, reading list and directory features
- Added intelligent extraction and bookmark configuration in frontend

### 3.2 Changed

- Modified `docker-compose.yml` to remove auto-start of WeChat-related services

### 3.3 Fixed

- Fixed bookmark batch processing notification during import


## 4 [1.1.3] - 2025-02-20

### 4.1 Added

- Support for TTS (Text to speech) in the data viewing interface and adding bookmarks
- Support for the browser's built-in speech synthesis engine
- Ability to add Chinese junior high school, high school, and high-frequency words to the vocabulary list

### 4.2 Changed

- Adjusted the frontend layout on mobile devices
- Fine-tuned the logic of the learning interface and the corresponding database, pre-installed example sentences for 5000 common words
- Modified the settings logic to allow any frontend interface to read cached settings

### 4.3 Fixed

- 401 error not redirecting to the re-login interface
- Fixed error in the word lookup interface


## 5 [1.1.4] - 2025-03-12

### 5.1 Added

- Added note editing interface
- Added AI and custom prompts
- Added table of contents support in the reading interface
- Added note-taking and note-exporting features in the reading interface
- Added feature to directly open clipboard

### 5.2 Changed

- Optimized TTS logic
- Optimized display format of epub files
- Optimized learning interface

### 5.3 Fixed

- Handling for Chat connection issues with the server

## 6 [1.2.0] - 2025-05-15

### 6.1 Added

- Added tree-like file list and preview functionality
- Added backend support for batch task processing
- Added image upload, editing, and OCR functionality to the text editing interface
- Added support for importing and extracting zip files
- Added support for converting other text formats to markdown

### 6.2 Changed

- Added OCR and REDIS services, please configure the environment variables in the .env file
- Updated the startup method of Docker Compose （`shell/*.sh`）
- Optimized the right-click menu in the "View" interface, adding translation, multi-color highlighting, and other features
- Improved code and image display in the "View" interface
- Reduced token usage when extracting information during file uploads
- When creating or uploading files, users can now select existing paths in addition to manual input

### 6.3 Fixed

- Fixed chapter order and table of contents formatting issues in epub files
- No longer adding prompts every time when chatting with the model
- Reduced translation time
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

- Integrated a comprehensive bookmark management UI, including navigation, search, "To-Read", and directory features.
- Backend now allows configuration of whether to extract text content using LLM, with additional settings for LLM truncation.
- Added LLM-based supplementary methods for extracting summaries from web pages.
- Introduced a feature to monitor and track bookmark click counts via the browser extension.  

### 3.2 Changed

- The bookmark source field has been changed from `web_chrome_bm` to `bookmark`.
- Changed the bookmark deletion logic to soft deletion (softly marks bookmarks as deleted).
- After editing bookmarks, the updated paths are now stored separately in both `mata` and `external path`.  
- Modify `docker-compose.yml` to remove the auto-start for `chatgpt-on-wechat` services.

### 3.3 Fixed

- Fixed an issue where the "todo" status was incorrectly assigned during bulk bookmark imports.
- Fixed the problem of duplicate bookmarks being imported.
- Fixed an issue with invalid bookmark path formats during import.
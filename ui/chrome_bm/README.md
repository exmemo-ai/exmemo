English | [中文简体](./README_cn.md)

# ExMemo Chrome Extension
An extension for synchronizing Google Chrome bookmarks.

## Features

Synchronization triggers: User manually clicks the extension's "Sync" button, or automatically syncs when bookmarks are created, deleted, modified, or moved.

- Synchronize bookmark list to the database, only adding the latest bookmarks during each sync
- Mark broken links

## Integration with the ExMemo Project (Important)

ExMemo is a personal knowledge management project aimed at unifying data storage, integrating information, and expanding cognitive capabilities. ExMemo chrome extension is a branch of the [ExMemo project](https://github.com/ExMemo/exmemo.git) and requires communication with the backend of the ExMemo project to store bookmark information. It also uses the project's frontend to support data retrieval and search across multiple platforms.

**Deploying the ExMemo Service**

Please refer to the project's [README.md](https://github.com/ExMemo/exmemo/blob/master/README.md) for setup and running instructions. The detailed steps are as follows:
- 2.1 Environment
- 2.2.1 Build Backend Image
- 2.2.2 Build Frontend Image
- 2.3.1 Start in Production Mode

## Installation and Setup

### Installation
1. Clone or download this repository.
2. Open Google Chrome and go to the extensions management page (enter `chrome://extensions/` in the address bar).
3. Enable "Developer mode" in the top right corner.
4. Click the "Load unpacked" button and select the `chrome_bm` folder.

### Setup
1. During the initial installation, enter the server address (`addr`), username, and password as prompted by the configuration page.
2. Switch Languages (Optional)
Language switch control: **Check and change the browser's language settings in Chrome**

- Open the Chrome browser.
- Click the three-dot icon (menu button) in the upper right corner.
- Select "Settings" from the menu.
- Enter "Language" in the search box. For example, to set English:
  - Click "Add languages," then select "English" in the dialog that appears, and click "Add."
  - Drag English to the top of the list, or click the three-dot icon on the right and select "Move to the top."
  - Ensure the ** "Display Google Chrome in this language" ** option is checked.
Restart the Chrome browser to apply the changes.

## Usage

Click the bookmark sync extension, then click the sync button and wait for the bookmarks to be synchronized to the database.
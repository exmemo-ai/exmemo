# Obsidian Plugin

`obsidian-exmemo-plugin` is an Obsidian plugin used for synchronization and retrieval.

## Compilation

To generate the ob plugin files, it relies on the `node:16-alpine` image.

```bash
docker run --name obdev --rm -v /exports:/exports -it node:16-alpine sh
cd /exports/exmemo/code/exmemo/ui/obsidian_plugin
npm install
npm run build # build to main.js
```

## Installation and Setup

### Installation

Copy the compiled main.js, manifest.json, and styles.css to the .obsidian/plugins/obsidian-exmemo-plugin directory in your Obsidian vault.

Make the following settings in Obsidian:

### Enable

Open "Settings" -> "Third-party Plugins."
Find "ExMemo" and click the enable button, then configure the settings.

### Settings

Server address format: http://IP:PORT
Username and password must match the frontend information.
Modify the included and excluded directories or files according to the prompts.

### Usage

Press Ctrl+P to bring up the plugin, type "ExMemo" in the search box, and then click on the desired Obsidian plugin feature.

### Note
Please back up your Obsidian data before syncing all files for the first time to avoid any unexpected issues.

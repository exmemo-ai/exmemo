import { TFile, PluginSettingTab, Setting, App, Events } from 'obsidian';
import { t } from "./lang/helpers"

export interface MindAnchorSettings {
	myUsername: string;
	myPassword: string;
	myToken: string;
	lastSync: Map<TFile, number>;
	lastSyncTime: number;
	url: string;
	include: string;
	exclude: string;
}

export const DEFAULT_SETTINGS: MindAnchorSettings = {
	myUsername: 'guest',
	myPassword: '123456',
	myToken: '',
	lastSync: new Map(),
	lastSyncTime: 0,
	url: 'http://localhost:8005',
	include: '',
	exclude: '',
}

export class MindAnchorSettingTab extends PluginSettingTab {
	plugin;

	constructor(app: App, plugin: any) {
		super(app, plugin);
		this.plugin = plugin;
	}

	display(): void {
		const { containerEl } = this;
		containerEl.empty();
		containerEl.createEl('h1', { text: t('general') });
		new Setting(containerEl)
			.setName(t('serverAddress'))
			.addText(text => text
				.setPlaceholder('http://localhost:8005')
				.setValue(this.plugin.settings.url)
				.onChange(async (value) => {
					this.plugin.settings.url = value;
					await this.plugin.saveSettings();
				}));
		new Setting(containerEl)
			.setName(t('username'))
			.addText(text => text
				.setPlaceholder(t('username'))
				.setValue(this.plugin.settings.myUsername)
				.onChange(async (value) => {
					this.plugin.settings.myUsername = value;
					await this.plugin.saveSettings();
				}));
		new Setting(containerEl)
			.setName(t('password'))
			.addText(text => text
				.setPlaceholder(t('password'))
				.setValue(this.plugin.settings.myPassword)
				.onChange(async (value) => {
					this.plugin.settings.myPassword = value;
					await this.plugin.saveSettings();
				}));
		new Setting(containerEl)
			.setName(t('include'))
			.addText(text => text
				.setPlaceholder('dir1, dir2, ... default is all')
				.setValue(this.plugin.settings.include)
				.onChange(async (value) => {
					this.plugin.settings.include = value;
					await this.plugin.saveSettings();
				}));
		new Setting(containerEl)
			.setName(t('exclude'))
			.addText(text => text
				.setPlaceholder('dir1, *_xxx.md default is null')
				.setValue(this.plugin.settings.exclude)
				.onChange(async (value) => {
					this.plugin.settings.exclude = value;
					await this.plugin.saveSettings();
				}));

	}
}
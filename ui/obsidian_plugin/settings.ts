import { PluginSettingTab, Setting, App } from 'obsidian';
import { t } from "./lang/helpers"

export interface ExMemoSettings {
	myUsername: string;
	myPassword: string;
	myToken: string;
	lastSyncTime: number;
	lastIndexTime: number;
	syncInterval: number;
	url: string;
	include: string;
	exclude: string;	
}

export const DEFAULT_SETTINGS: ExMemoSettings = {
	myUsername: 'guest',
	myPassword: '123456',
	myToken: '',
	lastSyncTime: 0,
	lastIndexTime: 0,
	syncInterval: 0,
	url: 'http://localhost:8005',
	include: '',
	exclude: '',
}

export class ExMemoSettingTab extends PluginSettingTab {
	plugin;

	constructor(app: App, plugin: any) {
		super(app, plugin);
		this.plugin = plugin;
	}

	display(): void {
		const { containerEl } = this;
		containerEl.empty();
		// 
        const fragment = document.createDocumentFragment();
        const link = document.createElement('a');
        link.href = 'https://github.com/ExMemo/exmemo/';
        link.text = 'GitHub project: exmemo';
        fragment.append(t('service_desc1'));
        fragment.append(link);
        fragment.append(t('service_desc2'));
		new Setting(containerEl)
			.setName(t('serverAddress'))
			.setDesc(fragment)
			.addText(text => text
				.setPlaceholder('http://localhost:8005')
				.setValue(this.plugin.settings.url)
				.onChange(async (value) => {
					this.plugin.settings.url = value;
					this.plugin.settings.myToken = '';
					await this.plugin.saveSettings();
				}));
		new Setting(containerEl)
			.setName(t('username'))
			.setDesc(t('username_desc'))
			.addText(text => text
				.setPlaceholder(t('username'))
				.setValue(this.plugin.settings.myUsername)
				.onChange(async (value) => {
					this.plugin.settings.myUsername = value;
					this.plugin.settings.myToken = '';
					await this.plugin.saveSettings();
				}));
		new Setting(containerEl)
			.setName(t('password'))
			.addText(text => text
				.setPlaceholder(t('password'))
				.setValue(this.plugin.settings.myPassword)
				.onChange(async (value) => {
					this.plugin.settings.myPassword = value;
					this.plugin.settings.myToken = '';
					await this.plugin.saveSettings();
				}).inputEl.type = 'password');
		new Setting(containerEl).setName(t('inexclude')).setHeading();
		new Setting(containerEl)
			.setName(t('include_name'))
			.setDesc(t('include_desc'))
			.addText(text => text
				.setPlaceholder('dir1, dir2, ... default is all')
				.setValue(this.plugin.settings.include)
				.onChange(async (value) => {
					this.plugin.settings.include = value;
					await this.plugin.saveSettings();
				}));
		new Setting(containerEl)
			.setName(t('exclude_name'))
			.setDesc(t('exclude_desc'))
			.addText(text => text
				.setPlaceholder('dir1, *_xxx.md default is null')
				.setValue(this.plugin.settings.exclude)
				.onChange(async (value) => {
					this.plugin.settings.exclude = value;
					await this.plugin.saveSettings();
				}));
		//		
		new Setting(containerEl).setName(t('auto_sync')).setHeading();
		new Setting(containerEl)
			.setName(t('auto_sync_interval'))
			.setDesc(t('auto_sync_interval_desc'))
			.addText(text => text
				.setPlaceholder('0')
				.setValue(this.plugin.settings.syncInterval.toString())
				.onChange(async (value) => {
					if (isNaN(parseInt(value))) {
						value = '0';
					}
					this.plugin.settings.syncInterval = parseInt(value);
					await this.plugin.saveSettings();
					this.plugin.resetSyncInterval();
				}));
	}
}
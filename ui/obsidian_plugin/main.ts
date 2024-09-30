import { Editor, MarkdownView, Plugin } from 'obsidian';
import { DEFAULT_SETTINGS, MindAnchorSettings, MindAnchorSettingTab } from 'settings';
import { Sync } from 'sync';
import { SearchModal } from 'search';
import { MindAnchorNotice } from 'notice';
import { t } from "./lang/helpers"

export default class MindAnchorPlugin extends Plugin {
	settings: MindAnchorSettings;
	notice: MindAnchorNotice;
	sync: Sync;

	async onload() {
		await this.loadSettings();
		this.notice = new MindAnchorNotice();
		this.sync = new Sync(this, this.app, this.settings);

		this.addCommand({
			id: 'exmemo-search',
			name: t('search'),
			editorCallback: (editor: Editor, view: MarkdownView) => {
				new SearchModal(this.app, this).open();
			}
		});
		this.addCommand({
			id: 'exmemo-upload',
			name: t('syncCurrentFile'),
			editorCallback: (editor: Editor, view: MarkdownView) => {
				this.sync.syncCurrentMd(this);
			}
		});
		this.addCommand({
			id: 'exmemo-sync',
			name: t('syncAllFiles'),
			editorCallback: (editor: Editor, view: MarkdownView) => {
				this.sync.syncAll();
			}
		});

		this.addSettingTab(new MindAnchorSettingTab(this.app, this));

		this.registerDomEvent(document, 'click', (evt: MouseEvent) => {
			console.log('click', evt);
		});

		// later add logic to sync add files
		this.registerInterval(window.setInterval(() => console.log('setInterval'), 5 * 60 * 1000));
	}

	showNotice(id: string, str: string, opts: any = {}) {
		this.notice.showInfo(id, str, opts)
	}

	hideNotice(id: string) {
		this.notice.hide(id);
	}

	onunload() {

	}

	async loadSettings() {
		this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
	}

	async saveSettings() {
		await this.saveData(this.settings);
	}

	async getMyToken() {
		this.showNotice('auth', t('login'));
		await new Promise(resolve => setTimeout(resolve, 3000));
		console.log('getMyToken');
		const url = new URL(this.settings.url + '/api/auth/login/');
		const requestOptions = {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				username: this.settings.myUsername,
				password: this.settings.myPassword
			})
		};
		try {
			const response = await fetch(url.toString(), requestOptions);
			if (response.ok) {
				const data = await response.json();
				console.log(data);
				this.settings.myToken = data.token;
				this.saveSettings();
				this.hideNotice('auth');
				return true
			}
		} catch (error) {
			console.error(error);
		}
		this.hideNotice('auth');
		this.showNotice('temp', t('loginFailed'), { timeout: 3000 });
		return false
	}

	parseError(err: any, show_notice: boolean = true) {
		if (err.status === 401) {
			this.settings.myToken = '';
			this.saveSettings();
			if (show_notice) {
				let showinfo = t('loginExpired') + ': ' + err.status;
				this.showNotice('error', showinfo, { timeout: 3000 });
			}
		} else {
			console.error(err);
			if (show_notice) {
				let showinfo = t('syncFailed') + ': ' + err.status;
				this.showNotice('error', showinfo, { timeout: 3000 });
			}
		}
	}
}
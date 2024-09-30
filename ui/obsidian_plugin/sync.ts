import * as fs from 'fs';
import * as path from 'path';
import { TFile, MarkdownView } from 'obsidian';
import { t } from "./lang/helpers"

const MD5 = require('crypto-js/md5');
const WordArray = require('crypto-js/lib-typedarrays');

export class Sync {
    app: any;
    settings: any;
    plugin: any;
    interrupt: boolean;
    interruptButton: any;
    localInfo: LocalInfo;

    constructor(plugin: any, app: any, settings: any) {
        this.plugin = plugin;
        this.app = app;
        this.localInfo = new LocalInfo(plugin, app);
        this.settings = settings;
        this.interrupt = false;
        this.interruptButton = {
            'text': t('interrupt'), 'callback': () => {
                console.log('interruptButton callback')
                this.interrupt = true;
            }
        };
    }

    async uploadFiles(uploadList: TFile[]) {
        const url = new URL(this.settings.url + '/api/entry/data/');
        const groupSize = 5;
        const groupCount = Math.ceil(uploadList.length / groupSize);
        let uploadedList: TFile[] = [];
        let ret = true;

        console.log('groupCount:', groupCount, 'groupSize:', groupSize, 'uploadList:', uploadList.length)
        //console.log(uploadList)

        this.plugin.showNotice('sync',
            t('upload') + ': ' + uploadedList.length + '/' + uploadList.length,
            { 'button': this.interruptButton });
        for (let i = 0; i < groupCount; i++) {
            // sleep 5 sec for test
            // await new Promise(resolve => setTimeout(resolve, 5000));
            if (this.interrupt) {
                break;
            }
            const group = uploadList.slice(i * groupSize, (i + 1) * groupSize);
            const requestOptions = {
                method: 'POST',
                headers: { 'Authorization': 'Token ' + this.settings.myToken },
                body: new FormData()
            };
            let file: TFile;
            for (file of group) {
                const fileContent = await this.app.vault.readBinary(file);
                const blob = new Blob([fileContent]);
                requestOptions.body.append('etype', 'note');
                requestOptions.body.append('source', 'obsidian_plugin');
                requestOptions.body.append('vault', this.app.vault.getName());
                requestOptions.body.append('rtype', 'upload');
                requestOptions.body.append('files', blob, file.name);
                requestOptions.body.append('filepaths', file.path);
                if (this.localInfo.fileInfoList[file.path]) {
                    requestOptions.body.append('filemd5s', this.localInfo.fileInfoList[file.path].md5);
                }
            }
            requestOptions.body.append('user_name', this.settings.myUsername);
            await fetch(url.toString(), requestOptions)
                .then(response => {
                    if (!response.ok) {
                        throw response;
                    }
                    return response.json();
                })
                .then(data => {
                    console.log(data);
                    if (data.list) {
                        for (const file of group) {
                            if (data.list.includes(file.path)) {
                                uploadedList.push(file);
                            }
                        }
                    }
                    if (data.emb_status) {
                        if (data.emb_status == 'failed') {
                            this.plugin.showNotice('error', t('embeddingFailed'), { timeout: 3000 });
                        }
                    }
                    this.plugin.showNotice('sync',
                        t('upload') + ': ' + uploadedList.length + '/' + uploadList.length,
                        { 'button': this.interruptButton });
                })
                .catch(err => {
                    this.plugin.parseError(err);
                    ret = false;
                });
        }
        console.log('uploadedList' + uploadedList.length)
        return [ret, uploadedList];
    }

    wildcardToRegex(wildcard: string) {
        let regex = wildcard.replace(/[.+^${}()|[\]\\]/g, '\\$&');
        regex = regex.replace(/\*/g, '.*');
        return new RegExp(regex);
    }

    async getLocalFiles() {
        // for syncall: get all files in vault, filter by include and exclude
        const include_list = this.settings.include.split(',');
        const exclude_list = this.settings.exclude.split(',');
        //const files = this.app.vault.getMarkdownFiles();
        const file_dict = await this.localInfo.getFileInfoList()

        console.log('vault total: ', Object.keys(file_dict).length)
        const fileList = [];
        //for (const file of files) {
        for (const key in file_dict) {
            const file = file_dict[key];
            //if (file.path.contains('.md')) {
            if (true) {
                let include = false;
                if (include_list.length == 0) {
                    include = true;
                } else {
                    for (const includePath of include_list) {
                        if (file.path.startsWith(includePath)) {
                            include = true;
                            break;
                        }
                    }
                }
                if (!include) {
                    continue;
                }
                for (const excludePath of exclude_list) {
                    let regex = this.wildcardToRegex(excludePath);
                    if (excludePath == '') {
                        break;
                    }
                    if (regex.test(file.path)) {
                        include = false;
                        break;
                    }
                }
                if (!include) {
                    //console.log('exclude2: ', file.path)
                    continue;
                }
                fileList.push({ 'path': file.path, 'mtime': file.mtime, 'md5': file.md5 });
            }
        }
        console.log('fileList total: ', fileList.length)
        return fileList;
    }

    async filterFiles(fileList: []) {
        // check md5, it has already moved to cloud, later move this function
        let filteredList: [] = [];
        for (const dic of fileList) {
            console.log('test', dic)
            if ('md5' in dic) {
                const file = this.app.vault.getAbstractFileByPath(dic['addr'])
                if (file == null) {
                    console.log('file not exist: ', dic['addr'])
                    filteredList.push(dic);
                } else {
                    await this.app.vault.read(file).then((content: any) => {
                        const md5 = MD5(content).toString();
                        if (md5 != dic['md5']) {
                            console.log('md5 not same: ', dic['addr'], 'loca', md5, 'remove', dic['md5'])
                            filteredList.push(dic);
                        } else {
                            console.log('md5 same: ', dic['addr'])
                        }
                    });
                }
            } else {
                filteredList.push(dic);
            }
        }
        console.log('filteredList: ', fileList.length, filteredList.length)
        return filteredList;
    }

    async syncAll(auto_login: boolean = true) {
        if (this.settings.myToken == '') {
            await this.plugin.getMyToken();
        }
        if (this.settings.myToken == '') {
            return;
        }
        const fileList = await this.getLocalFiles();
        const url = new URL(this.settings.url + '/api/sync/');
        const requestOptions = {
            method: 'POST',
            headers: { 'Authorization': 'Token ' + this.settings.myToken },
            body: new FormData()
        };
        requestOptions.body.append('user_name', this.settings.myUsername);
        requestOptions.body.append('vault', this.app.vault.getName());
        requestOptions.body.append('rtype', 'compare');
        requestOptions.body.append('include', this.settings.include);
        requestOptions.body.append('exclude', this.settings.exclude);
        requestOptions.body.append('last_sync_time', this.settings.lastSyncTime.toString())
        requestOptions.body.append('files', JSON.stringify(fileList));
        await fetch(url.toString(), requestOptions)
            .then(response => {
                //console.log('XXX')
                if (!response.ok) {
                    throw response;
                }
                return response.json();
            })
            .then(async (data): Promise<void> => {
                //console.log('BBB')
                //console.log(data);
                this.interrupt = false;
                let showinfo = ""
                let upload_list = data.upload_list;
                let download_list = data.download_list;
                let download_success = true;
                if (upload_list && upload_list.length > 0) {
                    //upload_list = await this.filterFiles(upload_list)
                    showinfo += t('upload') + ': ' + upload_list.length + ' ' + t('files') + '\n';
                }
                if (download_list && download_list.length > 0) {
                    //download_list = await this.filterFiles(download_list)
                    showinfo += t('download') + ': ' + download_list.length + ' ' + t('files') + '\n';
                }
                if (data.remove_list && data.remove_list.length > 0) {
                    showinfo += t('removeLocal') + ': ' + data.remove_list.length + ' ' + t('files') + '\n';
                }
                if (data.cloud_remove_list && data.cloud_remove_list.length > 0) {
                    showinfo += t('removeServer') + ': ' + data.cloud_remove_list.length + ' ' + t('files') + '\n';
                }
                if (showinfo == "") {
                    showinfo = t('nothingToDo');
                    this.plugin.showNotice('temp', showinfo, { timeout: 3000 });
                    console.log('syncAll nothing to do')
                    return;
                }
                this.plugin.showNotice('temp', showinfo, { timeout: 3000 });
                if (upload_list && upload_list.length > 0) {
                    let updateFiles: TFile[] = [];
                    for (const dic of upload_list) {
                        const file = this.app.vault.getAbstractFileByPath(dic['addr']);
                        if (file instanceof TFile) {
                            updateFiles.push(file);
                        }
                    }
                    await this.uploadFiles(updateFiles);
                }
                if (download_list && download_list.length > 0) {
                    download_success = await this.downloadFiles(download_list)
                }
                if (data.remove_list && data.remove_list.length > 0) {
                    await this.removeFiles(data.remove_list)
                }
                this.plugin.saveSettings();
                // wait 1 second to show
                await new Promise(resolve => setTimeout(resolve, 1000));
                this.plugin.showNotice('sync', t('syncFinished'), { timeout: 3000 });
                await this.localInfo.update();
                // lastSyncTime only affects file only in cloud
                // if file only in cloud, and lastSyncTime is new, remove cloud file
                // if download not success, maybe accidentally remove cloud file
                if (download_success) {
                    this.settings.lastSyncTime = new Date().getTime() + 5000; // 5 sec delay
                }
                console.log('syncAll finished')
            })
            .catch(err => {
                this.plugin.parseError(err, auto_login == false);
                if (err.status === 401) {
                    if (auto_login) {
                        this.syncAll(false);
                        return;
                    }
                }
                this.plugin.showNotice('sync', t('syncFailed'), { timeout: 3000 });
            });
    }

    async removeFiles(filelist: []) {
        for (const dic of filelist) {
            if (this.interrupt) {
                break;
            }
            try {
                await this.app.vault.adapter.remove(dic['addr']);
            } catch (error) {
                console.error(error);
            }
        }
    }

    async downloadFiles(filelist: []) {
        let count = 0
        let ret = true;
        for (const dic of filelist) {
            if (this.interrupt) {
                break;
            }
            ret = await this.downloadFile(dic['addr'], dic['idx']);
            if (!ret) {
                this.plugin.showNotice('temp', t('downloadFailed'), { timeout: 3000 });
                break;
            }
            count += 1;
            if (count % 5 == 0) {
                this.plugin.showNotice('sync',
                    t('download') + ': ' + count + '/' + filelist.length,
                    { 'button': this.interruptButton });
            }
        }
        this.plugin.showNotice('sync',
            t('download') + ': ' + count + '/' + filelist.length,
            { 'button': this.interruptButton });
        return ret;
    }

    async downloadFile(filename: string, idx: string) {
        console.log('downloadFile', filename, idx)
        let ret = true;
        const url = new URL(this.settings.url + '/api/entry/data/' + idx + '/' + 'download/');
        const requestOptions = {
            method: 'GET',
            headers: { 'Authorization': 'Token ' + this.settings.myToken }
        };
        await fetch(url.toString(), requestOptions)
            .then(async response => {
                if (!response.ok) {
                    throw response;
                }
                const blobData = await response.blob();
                return { blobData };
            })
            .then(async data => {
                const reader = new FileReader();
                reader.onload = async () => {
                    let absolutePath = path.join(this.app.vault.adapter.basePath, filename);
                    let dirname = path.dirname(absolutePath);
                    if (!fs.existsSync(dirname)) {
                        fs.mkdirSync(dirname, { recursive: true });
                    }
                    const arrayBuffer = await reader.result;
                    if (arrayBuffer instanceof ArrayBuffer) {
                        await this.app.vault.adapter.writeBinary(filename, arrayBuffer);
                    }
                };
                await reader.readAsArrayBuffer(data.blobData);
            })
            .catch(err => {
                this.plugin.parseError(err);
                ret = false;
            });
        return ret
    }

    async syncCurrentMd(plugin: any) {
        if (this.settings.myToken == '') {
            await this.plugin.getMyToken();
        }
        if (this.settings.myToken == '') {
            return;
        }
        this.interrupt = false;
        const file: TFile = this.app.workspace.getActiveViewOfType(MarkdownView).file;
        let [ret, list] = await this.uploadFiles([file]);
        this.plugin.hideNotice('sync')
        if (ret) {
            if (Array.isArray(list) && list.length > 0) {
                this.plugin.showNotice('temp', t('uploadSuccess'), { timeout: 3000 });
            } else {
                this.plugin.showNotice('temp', t('uploadFinished'), { timeout: 3000 });
            }
        }
    }
}

export class LocalInfo {
    plugin: any;
    app: any;
    fileInfoList: any;
    jsonPath: string;

    constructor(plugin: any, app: any) {
        this.plugin = plugin;
        this.app = app;
        this.fileInfoList = {};
        this.jsonPath = path.join(this.app.vault.adapter.getBasePath(), this.plugin.manifest.dir,
            this.app.vault.getName() + '_file_info.json');
        console.log('LocalInfo constructor:', this.jsonPath)
        this.load();
    }

    async getFileInfoList() {
        console.log('getFileInfoList() 1: ' + Object.keys(this.fileInfoList).length);
        await this.update();
        console.log('getFileInfoList() 2: ' + Object.keys(this.fileInfoList).length);
        return this.fileInfoList;
    }

    async update() {
        const vault = this.app.vault;
        const files = vault.getFiles();
        if (files.length == 0) {
            console.log('no vault files, wait for next update()')
            return;
        }
        this.plugin.showNotice('temp', 'ExMemo' + t('updateIndex'));
        //console.log('@@@ before local file update ' + Object.keys(this.fileInfoList).length);
        let count = 0;
        console.log('update() vault files: ' + files.length)
        for (const file of files) {
            const mtime = file.stat.mtime;
            if (file.path in this.fileInfoList) {
                if (this.fileInfoList[file.path].mtime == mtime) {
                    //console.log('skip:', file.path)
                    continue;
                }
            }

            const data = await vault.readBinary(file);
            const wordArray = WordArray.create(data);
            const md5Hash = MD5(wordArray).toString();
            //console.log(`MD5 hash: ${md5Hash}`);

            this.fileInfoList[file.path] = {
                path: file.path,
                md5: md5Hash,
                mtime: mtime
            };
            //console.log('add to filelist', md5Hash, file.path)
            count += 1;
        }
        for (const key in this.fileInfoList) {
            if (!files.find((file: TFile) => file.path == key)) {
                delete this.fileInfoList[key];
                count += 1;
            }
        }
        console.log('update count:', count, 'total:', Object.keys(this.fileInfoList).length)
        if (count > 0) {
            this.save();
        }
        console.log('@@@ after local file update ' + Object.keys(this.fileInfoList).length);
        this.plugin.hideNotice('temp')
    }

    save() {
        const fileInfoStr = JSON.stringify(this.fileInfoList, null, 2);
        const absolutePath = path.resolve(this.jsonPath);
        console.log('Saving to:', absolutePath);
        fs.writeFileSync(this.jsonPath, fileInfoStr);
    }

    async load() {
        if (fs.existsSync(this.jsonPath)) {
            const fileInfoStr = fs.readFileSync(this.jsonPath, 'utf8');
            this.fileInfoList = JSON.parse(fileInfoStr);
        }
        console.log('load file info:', Object.keys(this.fileInfoList).length)
        await this.update();
    }
}

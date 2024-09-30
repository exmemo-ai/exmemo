# Obsidian Plugin
`ExMemo` 是一个用于同步、检索的 Obsidian 插件。

## 编译
生成 ob 插件文件，依赖 `node:16-alpine` 镜像。
`yourfiles`路径需设为 exmemo 项目的上一级路径

```bash
docker run --name obdev --rm -v /yourfiles:/exports -it node:16-alpine sh
cd /exports/exmemo/ui/obsidian_plugin
echo "registry = http://registry.npm.taobao.org/" >> $HOME/.npmrc # 设置快速下载
npm install
npm run build # build main.js，会生成main.js文件
```

## 安装与设置

### 安装
将编译后的 `main.js`、`manifest.json` 和 `styles.css` 复制到 Obsidian 的 obsidian/plugins/obsidian_plugin 目录下。

在 ob 中进行以下设置：

### 启用
1. 打开「设置」->「第三方插件」
2. 找到「ExMemo」并点击启动按钮

### 设置
- 服务器地址格式：http://IP:PORT
- 用户名和密码需与前端信息一致
- 按提示修改包含目录和排除目录或文件

## 使用
按 Ctrl+P 调出插件，在检索框中输入 ExMemo，然后点击所需的ob插件功能。

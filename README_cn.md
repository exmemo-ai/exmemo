## 1 介绍

ExMemo 是一个个人知识管理项目旨在集中记录和管理各种信息，包括喜欢的文字、书籍、音乐、视频、网页、工作文档，以及对生活的感受和思考。甚至具体的物品位置、电话号码和地址等信息也能被自动分类，随时找到。通过系统化整合，突破思维的局限，寻找内在关联。

系统由数据库、后端和多个前端组成。分布式存储和数据库用于保存用户文件、文本及对应的向量数据。数据存储可本地部署，从而保护用户隐私。后端提供通用接口对数据进行增删改查，并负责调用大模型和处理数据。系统支持 OpenAI、Gemini、Qwen 等在线大模型及 Ollama 离线模型。多个前端以 Web 服务、微信机器人、Obsidian 插件和浏览器插件等形式供用户上传和下载数据。

此外，我还在数据框架的基础上添加了一些小工具，如计算热量、翻译和论文辅助阅读。这些工具展示了个人数据与大模型及工具结合后的效果。其他开发者也可以基于后端服务开发自己基于数据的应用。

## 2 操作安装

系统采用模块化管理。使用 PgVector 数据库、Python、JavaScript+VUE3 和 TypeScript 等语言实现。由于环境不同，系统被拆分成多个 Docker 镜像运行。用户只需编辑 docker-compose.yml 文件，即可启动所需的模块。

### 2.1 环境

下载源码，假设用户所有项目相关数据存放在 /exports/exmemo 目录中

``` shell
$ mkdir -p /exports/exmemo
$ cd /exports/exmemo
$ mkdir code
$ mkdir data
$ cd code
$ git clone https://github.com/ExMemo/exmemo.git
$ git clone https://github.com/zhayujie/chatgpt-on-wechat # if use wechat, download it
$ cd exmemo
```

根据 env_default 的格式配置用户个人的环境变量

``` shell
$ cp backend/env_default backend/.env
$ vi backend/.env
```

* 至少需要设置以下几个参数：IP 地址、LANGUAGE_CODE 和 PGSQL_PASSWORD。
* 建议使用 OpenAI 作为后端模型：
	* 如果可以连接 OpenAI，请设置 OPENAI_API_KEY。
	* 如果无法连接 OpenAI，例如在中国使用，可以将 DEFAULT_CHAT_LLM 和 DEFAULT_TOOL_LLM 设置为 deepseek，并配置 DEEPSEEK 部分。

### 2.2 制作镜像

#### 2.2.1 制作后端镜像

``` shell
$ cd backend
$ docker build -t exmemo:240927 .
$ docker tag exmemo:240927 exmemo:latest
$ cd ..
```

#### 2.2.2 制作前端镜像

``` shell
$ cd ui/web_frontend
$ docker build -t node_efrontend:240927 .
$ docker tag node_efrontend:240927 node_efrontend:latest
$ cd ../../
```

#### 2.2.3 微信插件

（可选）

``` shell
$ cd ui/wechat/
$ . install.sh # 复制插件到微信工具中
$ cd ../../
```

#### 2.2.4 Obsidian 插件

（可选）

根据需要编译 Obsidian 插件，并安装到 Obsidian 中。详见：ui/obsidian_plugin/README.md

### 2.3 启动服务

#### 2.3.1 以运行模式启动

```shell
$ docker-compose --env-file backend/.env --profile production up -d
```

此时打开 http://ip:8084/ 即可看到前端界面，使用时请先注册用户

#### 2.3.2 以开发模式启动

(可选)

如需要调试前后端代码，请以开发模型启动。

```shell
$ docker-compose --env-file backend/.env --profile development up -d
```

#### 2.3.3 S3 存储：minio

(可选)

默认情况下，数据存储在宿主机目录中。如果想使用 Minio S3 存储，请在.env 文件中设置相关的 MINIO 项。Minio Docker 默认不启动，如需在宿主机启动 Minio 服务，请手动操作。

```shell
$ docker-compose -f docker-compose-dev.yml up -d minio
```

#### 2.3.4 微信登录

(可选)

如果不使用微信操作，可跳过此步。作为 chatgpt-on-wechat 的插件连接 ExMemo 服务，具体原理请见项目：https://github.com/zhayujie/chatgpt-on-wechat

```shell
$ docker logs kwechat
```

扫描 logs 中的二维码登录。

用法：用户甲（机器人）通过扫码登录，其他用户可以通过与甲（机器人）的对话的方式与大模型聊天以及读写检索用户数据。如果您是第一次使用，请输入“帮助”以查看所有功能。

调试方法：运行程序时，确认 ExMemo 插件是否正常加载和初始化。如果无法正常初始化，请确认在 chatgpt-on-wechat/plugins/plugins.json 文件中，ExMemo 是否设置为 true。

### 2.4 升级

项目升级后，需要重新打包 Docker 镜像，并重新运行 Docker Compose。请注意，在重启时需删除旧容器，以避免出现不可预料的问题。操作如下：

```shell
$ docker-compose --env-file backend/.env down --volumes --remove-orphans
```

### 2.5 注意

* 打包时比较占内存。当云服务器资源较少时，最好释放一些资源。
* Docker-compose 中设置的数据库密码仅在建库时生效。如果之后需要修改密码，除了在 env 文件中进行更改外，还需要连接数据库并使用 SQL 语句进行修改。

## License

This project is licensed under the terms of the GNU Lesser General Public License v3.0. See the [LICENSE](./LICENSE) file for details.

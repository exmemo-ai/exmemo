FROM node:16-alpine

WORKDIR /opt/exmemo/ui/web_frontend

# 安装源码
COPY . /opt/exmemo/ui/web_frontend

# 安装依赖
RUN echo "registry = http://registry.npm.taobao.org/" >> $HOME/.npmrc \
    && npm install -g @vue/cli \
    && npm install vue-i18n \
    && npm install

# 启动时运行
CMD ["npm", "run", "serve"]

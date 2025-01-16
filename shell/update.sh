#!/bin/bash

DATE_STR=`date +%y%m%d`
PROXY_ADDR=http://192.168.10.168:12346
NO_PROXY="192.168.10.166,192.168.10.169,192.168.10.168,192.168.10.165"

cd /exports/exmemo/code/exmemo/
git pull
cd backend
docker build -t exmemo:$DATE_STR . --build-arg HTTP_PROXY=$PROXY_ADDR --build-arg HTTPS_PROXY=$PROXY_ADDR --build-arg NO_PROXY=$NO_PROXY
docker tag exmemo:$DATE_STR exmemo:latest
cd ../ui/web_frontend/
docker build -t node_efrontend:$DATE_STR . --build-arg HTTP_PROXY=$PROXY_ADDR --build-arg HTTPS_PROXY=$PROXY_ADDR --build-arg NO_PROXY=$NO_PROXY
docker tag node_efrontend:$DATE_STR node_efrontend:latest
cd ../wechat/
. install.sh
cd ../../
docker-compose --env-file backend/.env --profile production stop
docker-compose --env-file backend/.env down --volumes --remove-orphans
docker-compose --env-file backend/.env --profile production up -d

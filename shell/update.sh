#!/bin/bash

DATE_STR=`date +%y%m%d`
PROXY_ADDR="http://192.168.10.166:12346"
NO_PROXY="192.168.10.166,192.168.10.169,192.168.10.168,192.168.10.165"

echo "Stopping and removing existing containers..."
docker compose --env-file backend/.env --profile production down
docker compose --env-file backend/.env down --volumes --remove-orphans

echo "Removing any leftover containers..."
for container in efrontend efrontend_dev ebackend ebackend_dev edb ewechat eminio eredis; do
  docker rm -f $container 2>/dev/null || true
done

cd /exports/exmemo/code/exmemo/
git pull
cd backend
docker build --network=host -t exmemo:$DATE_STR . --build-arg HTTP_PROXY=$PROXY_ADDR --build-arg HTTPS_PROXY=$PROXY_ADDR --build-arg NO_PROXY=$NO_PROXY
docker tag exmemo:$DATE_STR exmemo:latest
cd ../ui/web_frontend/
docker build --network=host -t node_efrontend:$DATE_STR . --build-arg HTTP_PROXY=$PROXY_ADDR --build-arg HTTPS_PROXY=$PROXY_ADDR --build-arg NO_PROXY=$NO_PROXY
docker tag node_efrontend:$DATE_STR node_efrontend:latest
cd ../wechat/
. install.sh
cd ../../

echo "Starting new containers..."
docker compose --env-file backend/.env --profile production up -d

# UPDATE docker compose, remove DOCKER_BUILDKIT=1
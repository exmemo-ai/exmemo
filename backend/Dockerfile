# Build: docker build -t xieyan800811/ebackend:latest . --build-arg HTTP_PROXY=$HTTP_PROXY --build-arg HTTPS_PROXY=$HTTP_PROXY
# Run: docker run --rm -it --net=host xieyan800811/ebackend # 运行
# Dev: docker run --rm -it --net=host xieyan800811/ebackend bash # 开发

FROM python:3.11-slim

MAINTAINER XieYan

COPY sources.list /etc/apt/
RUN apt-get update -y --force-yes
RUN apt-get install git vim openssh-server -y --force-yes
RUN apt-get install gettext unrar -y --force-yes

#RUN echo '[global]' > /etc/pip.conf && \
#    echo 'index-url = https://mirrors.aliyun.com/pypi/simple/' >> /etc/pip.conf && \
#    echo 'trusted-host = mirrors.aliyun.com' >> /etc/pip.conf

COPY requirements.txt .
COPY data/sshd_config /etc/ssh/sshd_config
RUN pip3 install -r requirements.txt
RUN pip3 install git+https://github.com/openai/swarm.git
RUN echo "root:1" | chpasswd

COPY data/grpc.py /usr/local/lib/python3.11/site-packages/google/ai/generativelanguage_v1beta/services/generative_service/transports/grpc.py 
COPY data/grpc_asyncio.py /usr/local/lib/python3.11/site-packages/google/ai/generativelanguage_v1beta/services/generative_service/transports/grpc_asyncio.py 

COPY . /opt/exmemo/backend

WORKDIR /opt/exmemo/backend

CMD ["shell/run.sh"]

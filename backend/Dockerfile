# docker build -t exmemo:date .
# docker run --rm -it --net=host exmemo # 运行
# docker run --rm -it --net=host exmemo bash # 开发

FROM python:3.11

MAINTAINER XieYan

COPY sources.list /etc/apt/
RUN apt-get update -y --force-yes
RUN apt-get install vim openssh-server -y --force-yes
RUN apt-get install gettext -y --force-yes

RUN echo '[global]' > /etc/pip.conf && \
    echo 'index-url = https://mirrors.aliyun.com/pypi/simple/' >> /etc/pip.conf && \
    echo 'trusted-host = mirrors.aliyun.com' >> /etc/pip.conf

COPY requirements.txt .
COPY data/sshd_config /etc/ssh/sshd_config
RUN pip3 install -r requirements.txt
RUN echo "root:1" | chpasswd

COPY data/grpc.py /usr/local/lib/python3.11/site-packages/google/ai/generativelanguage_v1beta/services/generative_service/transports/grpc.py 
COPY data/grpc_asyncio.py /usr/local/lib/python3.11/site-packages/google/ai/generativelanguage_v1beta/services/generative_service/transports/grpc_asyncio.py 

COPY . /opt/exmemo/backend

WORKDIR /opt/exmemo/backend

CMD ["python", "manage.py", "runserver", "0.0.0.0:8005"]

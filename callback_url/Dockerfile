FROM python:3.6

RUN echo "Asia/Shanghai" > /etc/timezone && dpkg-reconfigure -f noninteractive tzdata
RUN pip install \
    --index-url=http://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host=mirrors.aliyun.com \
    --upgrade wheel

COPY requirements.txt /fenle/
RUN pip install \
    --index-url=http://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host=mirrors.aliyun.com \
    -r /fenle/requirements.txt

WORKDIR /fenle/callback_url/
CMD ["uwsgi", "uwsgi.ini"]

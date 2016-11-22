FROM liyuan462/ubuntu:trusty-py

COPY requirements.txt /jidui/
RUN pip install -r /jidui/requirements.txt
COPY . /jidui/
COPY api/docker/test/wait-for-postgres.py /jidui/api/
WORKDIR /jidui/api/

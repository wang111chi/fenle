FROM liyuan462/ubuntu:trusty-py

COPY requirements.txt /jidui/
RUN pip install -r /jidui/requirements.txt
COPY . /jidui/
COPY docker/wait-for-postgres.py /jidui/tests/
WORKDIR /jidui/tests/
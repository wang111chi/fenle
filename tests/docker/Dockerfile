FROM liyuan462/ubuntu:trusty-py

COPY requirements.txt /fenle/
RUN pip install -r /fenle/requirements.txt
COPY . /fenle/
COPY docker/wait-for-mysql.py /fenle/tests/
WORKDIR /fenle/tests/
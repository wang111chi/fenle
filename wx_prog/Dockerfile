FROM liyuan462/ubuntu:trusty-py

COPY requirements.txt /fenle/
RUN pip install -r /fenle/requirements.txt
WORKDIR /fenle/wx_prog/
CMD ["uwsgi", "uwsgi.ini"]

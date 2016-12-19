FROM liyuan462/ubuntu:trusty-py

COPY requirements.txt /fenle/
RUN pip install -r /fenle/requirements.txt
WORKDIR /fenle/callback_url/
CMD ["uwsgi", "uwsgi.ini"]

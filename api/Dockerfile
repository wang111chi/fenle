FROM liyuan462/ubuntu:trusty-py

COPY requirements.txt /jidui/
RUN pip install -r /jidui/requirements.txt
WORKDIR /jidui/api/
CMD ["uwsgi", "uwsgi.ini"]

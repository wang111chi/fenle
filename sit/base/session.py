#!/usr/bin/env python
# -*- coding:utf-8 -*-


import os
import string
import pickle
from datetime import timedelta
import json

from redis import Redis
from werkzeug.datastructures import CallbackDict
from flask.sessions import SessionInterface, SessionMixin


class RedisSession(CallbackDict, SessionMixin):
    def __init__(self, initial=None, sid=None, new=False):
        def on_update(self):
            self.modified = True
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.new = new
        self.modified = False


class RedisSessionInterface(SessionInterface):
    serializer = pickle
    session_class = RedisSession

    def __init__(self, redis=None, prefix='session:'):
        if redis is None:
            redis = Redis()

        self.redis = redis
        self.prefix = prefix

    def generate_sid(self):
        # return str(uuid4())
        chars = string.ascii_letters + string.digits + "_-"
        return "".join([chars[i % len(chars)] for i in os.urandom(40)])

    def get_redis_expiration_time(self, app, session):
        if session.permanent:
            return app.permanent_session_lifetime
        return timedelta(hours=1)

    def open_session(self, app, request):
        sid = request.headers.get("X-SessionId")
        if not sid:
            sid = self.generate_sid()
            return self.session_class(sid=sid, new=True)
        val = self.redis.get(self.prefix + sid)
        if val is not None:
            data = self.serializer.loads(val)
            return self.session_class(data, sid=sid)
        return self.session_class(sid=sid, new=True)

    def save_session(self, app, session, response):
        if not session:
            self.redis.delete(self.prefix + session.sid)
            return

        redis_exp = self.get_redis_expiration_time(app, session)

        ttl = int(redis_exp.total_seconds())

        val = self.serializer.dumps(dict(session))
        self.redis.setex(self.prefix + session.sid,
                         ttl,
                         val)

        d = json.loads(response.get_data())
        d['session_id'] = session.sid
        d['session_ttl'] = ttl
        response.set_data(json.dumps(d))

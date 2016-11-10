#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import wraps

from flask import make_response, render_template, redirect, request

import config
from base import logger
from base.db import engine
from base import util
from base import constant as const


def general(desc):
    def deco(old_handler):
        @wraps(old_handler)
        def new_handler(*args, **kwargs):
            resp = old_handler(*args, **kwargs)

            if isinstance(resp, TempResponse):
                # 添加自定义变量
                resp.context_update(
                    const=const,
                )

            if isinstance(resp, Response):
                output = resp.output()
                if config.DEBUG:
                    logger.get("response-log").debug("u[%s] %s" % (
                        request.url, output.get_data(as_text=True)))
                return output
            return resp

        new_handler.desc = desc
        new_handler.is_handler = True
        return new_handler
    return deco


class Response(object):
    def __init__(self):
        self._ext_header = {}
        self._ext_cookie = {}

    def set_header(self, key, value):
        self._ext_header[key] = value

    def set_cookie(self, key, value, **kwargs):
        self._ext_cookie[key] = (value, kwargs)

    def output(self):
        resp = make_response(self._output())

        for k, v in self._ext_header.iteritems():
            resp.headers[k] = v

        for k, v in self._ext_cookie.iteritems():
            resp.set_cookie(k, v[0], **v[1])

        return resp

    def _output(self):
        return "", 404


class JsonResponse(Response):
    def __init__(self, **kwargs):
        Response.__init__(self)
        self._ext_header["Content-Type"] = "application/json"
        self._json = {} if kwargs is None else kwargs

    def _output(self):
        return util.safe_json_dumps(self._json)


class TempResponse(Response):
    def __init__(self, template_name, **context):
        Response.__init__(self)
        self._ext_header["Content-Type"] = "text/html"
        self._template_name = template_name
        self._context = context

    def context_update(self, **kwargs):
        self._context.update(kwargs)

    def _output(self):
        return render_template(self._template_name, **self._context)


def db_conn(old_handler):
    @wraps(old_handler)
    def new_handler(*args, **kwargs):
        kwargs.update(db=engine.connect())
        return old_handler(*args, **kwargs)

    return new_handler

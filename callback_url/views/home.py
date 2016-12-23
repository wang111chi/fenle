#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

from flask import Blueprint
from flask import request
import gevent
import requests

from base.framework import general, db_conn, form_check, JsonOkResponse
from base.db import engine, t_callback_url
from base import util
from base import logic
from base import logger
from base.xform import F_str, F_int
from base import constant as const

home = Blueprint("home", __name__)


@home.route("/callback_url")
@general("首页")
@db_conn
@form_check({
    # 请求URL，必填
    "url": (F_str("URL") <= 2000) & "strict" & "required",
    # 请求方法，默认为const.HTTP_METHOD.GET
    "method": ((F_int("HTTP method", const.HTTP_METHOD.GET)) & "strict" &
               "required" & (lambda v: (v in const.HTTP_METHOD.ALL, v))),
    # 请求body，如果请求方法为const.HTTP_METHOD.GET，则忽略此参数
    "body": (F_str("HTTP body")) & "strict" & "optional",
    # 请求模式，必填，详见const.CALLBACK_URL.MODE
    "mode": (F_int("模式") & "strict" & "required" & (
        lambda v: (v in const.CALLBACK_URL.MODE.ALL, v)))
})
def callback(db, safe_vars):
    now = datetime.datetime.now()

    stmt = t_callback_url.insert().values(
        url=safe_vars['url'],
        method=safe_vars['method'],
        body=safe_vars['body'],
        ip=util.safe_inet_aton(request.remote_addr),
        mode=safe_vars['mode'],
        create_time=now,
    )

    callback_id = db.execute(stmt).inserted_primary_key[0]

    gevent.spawn(
        do_callback, callback_id,
        safe_vars['mode'], safe_vars['url'],
        safe_vars['method'], safe_vars['body'])

    return JsonOkResponse()


def do_callback(callback_id, mode, url,
                method=const.HTTP_METHOD.GET, body=None):

    now = datetime.datetime.now()

    is_success, resp_code, resp_body = logic.callback_url(
        callback_id, mode, url, method=method, body=body)

    if is_success:
        status = const.CALLBACK_URL.STATUS.DONE
    else:
        status = const.CALLBACK_URL.STATUS.PENDING

    db = engine.connect()

    stmt = t_callback_url.update().where(
        t_callback_url.c.id == callback_id
    ).values(
        resp_code=resp_code,
        resp_body=resp_body,
        call_time=now,
        is_call_success=const.BOOLEAN.TRUE if
        is_success else const.BOOLEAN.FALSE,
        status=status
    )

    db.execute(stmt)

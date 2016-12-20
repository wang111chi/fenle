#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

from flask import Blueprint
from flask import request

from base.framework import general, db_conn, form_check, JsonOkResponse
from base.db import t_callback_url
from base import util
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
    "method": ((F_int("HTTP method", const.HTTP_METHOD.GET))  & "strict" &
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

    db.execute(stmt)

    return JsonOkResponse()


#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

from flask import Blueprint, session
from flask import request
import gevent
import requests

from base.framework import general, db_conn, form_check, JsonOkResponse
from base.framework import JsonErrorResponse
from base.db import engine, t_callback_url
from base import util
from base import logic
from base import logger
from base import constant as const

home = Blueprint("home", __name__)


@home.route("/")
@general("测试")
def index():
    open_id = session.get(const.SESSION.KEY_WX_PROG_OPENID)
    if open_id is None:
        return JsonErrorResponse("用户未登录",
                                 status=const.REQUEST_STATUS.AUTH_ERROR)

    return JsonOkResponse(u"用户已登录，OpenID: %s" % (open_id, ))

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, session
import requests

import config
from base.framework import form_check, general
from base.framework import JsonErrorResponse, JsonOkResponse
from base.xform import F_mobile, F_str, F_int
from base import logger
from base import constant as const

user = Blueprint("user", __name__)


@user.route("/user/login")
@general("登录")
@form_check({
    "code": F_str("code") & "strict" & "required",
})
def login(safe_vars):
    url = "https://api.weixin.qq.com/sns/jscode2session"
    payload = {
        "appid": config.APP_ID,
        "secret": config.APP_SECRET,
        "js_code": safe_vars["code"],
        "grant_type": "authorization_code",
    }
    r = requests.get(url, params=payload)
    r = r.json()
    if "errcode" in r:
        logger.error("[call api failed]: <api url>=><%s>, <errcode>=><%s>, "
                     "<errmsg>=><%s>", url, r["errcode"], r["errmsg"])
        return JsonErrorResponse(u"登录失败")

    # 到这里微信那边登录成功，服务端保存session
    session[const.SESSION.KEY_WX_PROG_SESSION_KEY] = r["session_key"]
    session[const.SESSION.KEY_WX_PROG_OPENID] = r["openid"]
    session.permanent = True

    return JsonOkResponse()

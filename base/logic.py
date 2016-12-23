#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests

from base import logger
from base import constant as const


def callback_url(callback_id,
                 mode,
                 url,
                 method=const.HTTP_METHOD.GET,
                 body=None,
                 logger=logger.get("cgi-log")):
    u"""回调URL.

    @param<callback_id>: 回调在数据库中的ID(对应的表为callback_url)
    @param<mode>: 回调模式，详见const.CALLBACK_URL.MODE
    @param<url>: 回调的URL
    @param<method>: 回调的HTTP方法
    @param<body>: 如果回调方法为POST， 则为需要POST的HTTP body
    @param<logger>: 用于记日志的对象

    @return: (is_sucess,   # 回调是否成功
              resp_code,   # 回调的HTTP响应状态码
              resp_body,   # 回调的HTTP响应body
             )
    """
    http_method = requests.get

    if method == const.HTTP_METHOD.POST:
        http_method = requests.post

    resp_code = None
    resp_body = None

    try:
        if body is None:
            r = http_method(url)
        else:
            r = http_method(url, body)
    except Exception:
        logger.error("[callback request error]: "
                     "<callback_id>=><%s>, <url>=><%s>",
                     callback_id, url, exc_info=True)
        is_success = False
    else:
        resp_code = r.status_code
        resp_body = r.content
        is_success = callback_url_resp_check(r, mode)

    return is_success, resp_code, resp_body


def callback_url_resp_check(resp, mode):
    u"""回调URL的结果检查，根据响应确定回调是否成功.

    @param resp: requests的响应,
                 http://docs.python-requests.org/en/master/api/#requests.Response # noqa
    @param mode: 回调URL的模式，详见const.CALLBACK_URL.MODE
    """
    if resp.status_code != 200:
        return False

    # TODO: judge according to mode
    try:
        json_resp = resp.json()
    except ValueError:
        return False

    if json_resp.get('retcode') == 0:
        return True

    return False

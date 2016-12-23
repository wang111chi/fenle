#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wsgi_handler

import json
import urllib

from base.fixtures import *
from base.db import t_callback_url
from base import constant as const


def test_callback_get(client, db):
    result = db.execute(t_callback_url.select())
    assert result.first() is None

    resp = client.get('/callback_url', query_string={
        "url": "http://www.baidu.com",
        "mode": const.CALLBACK_URL.MODE.CARDPAY_APPLY_SUCCESS_NOTIFY,
    })

    assert resp.status_code == 200

    json_resp = json.loads(resp.data)
    assert json_resp["status"] == const.REQUEST_STATUS.SUCCESS


def test_callback_post(client, db):
    resp = client.get('/callback_url', query_string={
        "url": "http://www.baidu.com",
        "method": const.HTTP_METHOD.POST,
        "mode": const.CALLBACK_URL.MODE.CARDPAY_APPLY_SUCCESS_NOTIFY,
    })

    assert resp.status_code == 200

    json_resp = json.loads(resp.data)
    assert json_resp["status"] == const.REQUEST_STATUS.SUCCESS

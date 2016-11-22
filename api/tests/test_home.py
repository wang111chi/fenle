#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import operator
import hashlib
from base64 import b64encode
import json

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Signature import PKCS1_v1_5 as sign_PKCS1_v1_5
from Crypto.Hash import SHA
import pytest

import wsgi_handler
from base import util
import config


class TestCardpayApply(object):
    def test_cardpay_apply_md5(self, client):
        u"""MD5签名 + RSA加密"""

        # 分配给商户的key
        key = "123456"

        # 参数
        params = {
            "encode_type": "MD5",
            "spid": "1" * 10,
        }

        params = params.items()
        params = [(k, v) for k, v in params if
                  v is not None and v != ""]
        params = sorted(params, key=operator.itemgetter(0))
        params_with_key = params + [("key", key)]

        urlencoded_params = urllib.urlencode(params_with_key)

        # MD5签名
        m = hashlib.md5()
        m.update(urlencoded_params)
        sign = m.hexdigest()

        # RSA加密
        params_with_sign = params + [("sign", sign)]
        urlencoded_params = urllib.urlencode(params_with_sign)

        cipher_data = b64encode(
            util.rsa_encrypt(urlencoded_params, config.JIDUI_PUB_KEY))

        final_params = {"cipher_data": cipher_data}
        final_params = urllib.urlencode(final_params)

        resp = client.get('/cardpay/apply?%s' % final_params)

        assert resp.status_code == 200

    def test_cardpay_apply_rsa(self, client):
        u"""RSA签名 + RSA加密"""

        # 参数
        params = {
            "encode_type": "RSA",
            "spid": "1" * 10,
        }

        # RSA签名 + RSA加密
        cipher_data = util.rsa_sign_and_encrypt_params(
            params,
            config.TEST_MERCHANT_PRIVATE_KEY,
            config.JIDUI_PUB_KEY
        )

        final_params = urllib.urlencode({"cipher_data": cipher_data})
        resp = client.get('/cardpay/apply?%s' % final_params)

        assert resp.status_code == 200
        data = json.loads(resp.data)
        print data


@pytest.fixture()
def app():
    wsgi_handler.app.config["TESTING"] = True
    return wsgi_handler.app


@pytest.fixture()
def client(app):
    return app.test_client()

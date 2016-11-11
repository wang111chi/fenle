#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import urllib
import operator
import hashlib

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import pytest

import wsgi_handler


class TestCardpayApply(object):
    def test_cardpay_apply_md5(self, client):
        u"""MD5签名 + RSA加密"""

        # 分配给商户的key
        key = "123456"

        # 参数
        params = {
            "c": "",
            "a": "xx",
            "b": "xx",
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

        pub_key = open(
            os.path.join(
                os.path.split(
                    os.path.split(os.path.realpath(__file__))[0])[0],
                "config", "id_isa_pub.pub")).read()

        pub_key = RSA.importKey(pub_key)
        cipher = PKCS1_v1_5.new(pub_key)
        cipher_data = pkcs_encrypt(cipher, urlencoded_params)

        final_params = {"cipher_data": cipher_data}
        final_params = urllib.urlencode(final_params)

        resp = client.get('/cardpay/apply?%s' % final_params)

        assert resp.status_code == 200


def pkcs_encrypt(cipher, message):
    handled = 0
    ciphertext = ""
    while len(message[handled:]) > 0:
        part = message[handled:handled + 117]
        ciphertext += cipher.encrypt(part)
        handled += len(part)
    return ciphertext


@pytest.fixture()
def app():
    wsgi_handler.app.config["TESTING"] = True
    return wsgi_handler.app


@pytest.fixture()
def client(app):
    return app.test_client()

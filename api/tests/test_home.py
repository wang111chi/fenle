#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import operator
import hashlib
from base64 import b64encode

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Hash.SHA import SHA1Hash
import pytest

import wsgi_handler
import config


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

        jidui_pub_key = RSA.importKey(config.JIDUI_PUB_KEY)
        cipher = PKCS1_v1_5.new(jidui_pub_key)
        cipher_data = pkcs_encrypt(cipher, urlencoded_params)

        final_params = {"cipher_data": cipher_data}
        final_params = urllib.urlencode(final_params)

        resp = client.get('/cardpay/apply?%s' % final_params)

        assert resp.status_code == 200

    def test_cardpay_apply_rsa(self, client):
        u"""RSA签名 + RSA加密"""

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
        urlencoded_params = urllib.urlencode(params)

        # RSA签名
        sha1 = SHA1Hash()
        sha1.update(urlencoded_params)
        sha1_params = sha1.digest()
        merchant_private_key = RSA.importKey(config.TEST_MERCHANT_PRIVATE_KEY)
        cipher = PKCS1_v1_5.new(merchant_private_key)
        cipher_data = pkcs_encrypt(cipher, sha1_params)
        sign = b64encode(cipher_data)

        # RSA加密
        params_with_sign = params + [("sign", sign)]
        urlencoded_params = urllib.urlencode(params_with_sign)

        jidui_pub_key = RSA.importKey(config.JIDUI_PUB_KEY)
        cipher = PKCS1_v1_5.new(jidui_pub_key)
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

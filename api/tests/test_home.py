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
from base.db import engine, meta
from base.db import t_merchant_info
from base.db import t_bank_channel
from base.db import t_sp_bank
import config
from base import logger
from base import constant as const


class TestCardpayApply(object):
    # 测试参数模板
    params = util.encode_unicode({
        "encode_type": "MD5",
        "spid": "1" * 9 + '1',
        "sp_userid": "12345678",
        "sp_tid": "1234567",
        "money": 12345,
        "cur_type": 1,
        "notify_url": "FIXME",
        "errpage_url": "",
        "memo": u"测试商品",
        "expire_time": "",
        "attach": "wang",
        "user_account_type": 1,
        "user_account_attr": 1,
        "user_account_no": "1234567890123456",
        "user_name": u"张三",
        "bank_type": "1001",
        "user_mobile": "13312345678",
        "expiration_date": "2020-05",
        "pin_code": "9376",
        "divided_term": 6,
        "fee_duty": 1,
        "channel": 1,
        "rist_ctrl": "",
    })

    def insert_bank_and_merchant(self, conn):
        """ insert some test data to mysql table"""

        # initial merchant_info
        merchant_data = dict(
            spid='1' * 10,
            uid='111',
            agent_uid='112',
            parent_uid='113',
            status=0,
            sp_name='guazi',
            mer_key='654321' * 3,
            rsa_pub_key="""\
-----BEGIN PUBLIC KEY--@pytest.fix---
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDWXsFnKxKhPDofiexxxjmfYLWo
4dkKzbuTSC0teqpQ4YmeCBJNcLDbGB+WuHRAKEd1xU6UrVSlfm/YWQ5ycimraeVi
masD9WDizyvKgNMUWBZoa7TgDRJ4SLPq/Fb1skKagUlrWtaDCqfoCHZ73RPcjeQK
//kY7Csyw/s18GpS2wIDAQAB
-----END PUBLIC KEY-----"""
        )
        ins = t_merchant_info.insert()
        conn.execute(ins, merchant_data)

        # initial sp_bank data
        sp_bank_data = dict(
            spid='1' * 10,
            bank_type=1001,
            fenqi_fee_percent=json.dumps({6: 500, 12: 600}),
            divided_term='6,12',
            settle_type=const.SETTLE_TYPE.DAY_SETTLE, )
        conn.execute(t_sp_bank.insert(), sp_bank_data)

        # initial bank_channel data
        bank_data = dict(
            bank_channel=1,
            bank_type=1001,
            is_enable=1,
            bank_valitype=0x0002,
            fenqi_fee_percent=json.dumps({6: 300, 12: 400}),
            rsp_time=10,
            settle_type=const.SETTLE_TYPE.DAY_SETTLE, )
        conn.execute(t_bank_channel.insert(), bank_data)

    def test_cardpay_apply_md5(self, client, db):
        u"""MD5签名 + RSA加密."""
        # 插入初始数据
        self.insert_bank_and_merchant(db)

        # 分配给商户的key
        key = "654321" * 3

        params = self.params.items()
        params = [(k, v) for k, v in params if
                  v is not None and v != ""]
        params = sorted(params, key=operator.itemgetter(0))
        params_with_key = params + [("key", key)]

        urlencoded_params = urllib.urlencode(params_with_key)
        logger.debug(urlencoded_params)
        # MD5签名
        m = hashlib.md5()
        m.update(urlencoded_params)
        sign = m.hexdigest()

        # RSA加密
        params_with_sign = params + [("sign", sign)]
        urlencoded_params = urllib.urlencode(params_with_sign)

        cipher_data = b64encode(
            util.rsa_encrypt(urlencoded_params, config.FENLE_PUB_KEY))

        final_params = {"cipher_data": cipher_data}
        final_params = urllib.urlencode(final_params)

        resp = client.get('/cardpay/apply?%s' % final_params)

        assert resp.status_code == 200

        json_resp = json.loads(resp.data)
        print json_resp
        assert json_resp["retcode"] == 0

    def test_cardpay_apply_rsa(self, client):
        u"""RSA签名 + RSA加密."""
        params = self.params

        # RSA签名 + RSA加密
        cipher_data = util.rsa_sign_and_encrypt_params(
            params,
            config.TEST_MERCHANT_PRIVATE_KEY,
            config.FENLE_PUB_KEY
        )

        final_params = urllib.urlencode({"cipher_data": cipher_data})
        resp = client.get('/cardpay/apply?%s' % final_params)

        assert resp.status_code == 200

        # json_resp = json.loads(resp.data)
        # assert json_resp["retcode"] == 0


@pytest.fixture()
def app():
    wsgi_handler.app.config["TESTING"] = True
    return wsgi_handler.app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    conn = engine.connect()
    # clear all tables
    for table in reversed(meta.sorted_tables):
        conn.execute(table.delete())
    return conn

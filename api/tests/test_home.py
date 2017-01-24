#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import operator
import hashlib
from base64 import b64encode
from base64 import b64decode
import json

from datetime import datetime
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Signature import PKCS1_v1_5 as sign_PKCS1_v1_5
from Crypto.Hash import SHA
from sqlalchemy.sql import text, select
import pytest
from flask import Flask

import wsgi_handler
from base import util
from base.db import engine, meta
from base.db import t_merchant_info
from base.db import t_bank_channel
from base.db import t_sp_bank
from base.db import t_sp_balance
from base.db import t_fenle_balance
import config
from base import logger
from base import constant as const
from base.framework import ApiJsonErrorResponse
from base.framework import general, api_form_check
from base.xform import F_str


class TestCardpayApply(object):
    # 测试参数模板

    params = {
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
        "useless": "what",
    }
    spid = '1' * 10
    bank_type = 1001
    sp_private_key = config.TEST_MERCHANT_PRIVATE_KEY

    def insert_bank_and_merchant(self, conn):
        """insert some test data to mysql table."""
        # initial merchant_info
        merchant_data = {
            'spid': self.spid,
            'uid': '111',
            'mer_key': '654321' * 3,
            'agent_uid': '112',
            'parent_uid': '113',
            'status': 0,
            'sp_name': 'guazi',
            'rsa_pub_key': config.TEST_MERCHANT_PUB_KEY}
        ins = t_merchant_info.insert()
        conn.execute(ins, merchant_data)

        # initial sp_bank data
        sp_bank_data = {
            'spid': self.spid,
            'bank_spid': self.spid + '12345',
            'bank_type': self.bank_type,
            'fenqi_fee_percent': json.dumps({6: 500, 12: 600}),
            'divided_term': '6,12',
            'settle_type': const.SETTLE_TYPE.DAY_SETTLE}
        conn.execute(t_sp_bank.insert(), sp_bank_data)

        # initial bank_channel data
        bank_data = {
            'bank_channel': 1,
            'bank_type': self.bank_type,
            'is_enable': 1,
            # 修改此处决定是否验证手机号
            'bank_valitype': const.BANK_VALITYPE.MOBILE_VALID,
            'fenqi_fee_percent': json.dumps({6: 300, 12: 400}),
            'rsp_time': 10,
            'settle_type': const.SETTLE_TYPE.DAY_SETTLE}
        conn.execute(t_bank_channel.insert(), bank_data)
        return bank_data['bank_valitype'],

    def init_balance(self, conn):
        """insert some test data to mysql table."""
        now = datetime.now()
        # initial sp_balance
        sp_balance_data = {
            'spid': self.spid,
            'cur_type': self.params['cur_type'],
            'uid': self.spid,
            'b_balance': 0,
            'modify_time': now,
            'create_time': now}
        conn.execute(t_sp_balance.insert(), sp_balance_data)
        # initial fenle_balance
        fenle_balance_data = {
            'account_no': config.FENLE_ACCOUNT_NO,
            'bank_type': config.FENLE_BANK_TYPE,
            'account_type': const.FENLE_ACCOUNT.VIRTUAL,
            'modify_time': now,
            'create_time': now}
        conn.execute(t_fenle_balance.insert(), fenle_balance_data)

    def cardpay_apply_md5(self, key, params):
        u"""MD5签名 + RSA加密."""
        params = [(k, v) for k, v in params.items() if
                  v is not None and v != ""]
        params = sorted(params, key=operator.itemgetter(0))
        params_with_key = params + [("key", key)]

        urlencoded_params = urllib.parse.urlencode(params_with_key)
        # MD5签名
        m = hashlib.md5()
        m.update(urlencoded_params.encode())
        sign = m.hexdigest()

        # RSA加密
        params_with_sign = params + [("sign", sign)]
        urlencoded_params = urllib.parse.urlencode(params_with_sign)

        cipher_data = b64encode(
            util.rsa_encrypt(urlencoded_params, config.FENLE_PUB_KEY))

        return {"cipher_data": cipher_data}

    def test_cardpay_apply_md5(self, client, db):
        bank_valitype = self.insert_bank_and_merchant(db)
        self.init_balance(db)

        # 分配给商户的key, 用于MD5 签名
        key = "654321" * 3
        # 支付请求
        query_params = self.cardpay_apply_md5(key, self.params)
        resp = client.get('/cardpay/apply', query_string=query_params)

        assert resp.status_code == 200
        json_resp = json.loads(resp.data)

        assert json_resp["retcode"] == 0
        params = util.rsa_decrypt(
            json_resp['cipher_data'],
            config.TEST_MERCHANT_PRIVATE_KEY)
        list_id = params['list_id'][0]

        # 支付确认
        if bank_valitype == const.BANK_VALITYPE.MOBILE_VALID:
            confirm_data = {
                "encode_type": "MD5",
                "list_id": list_id,
                "spid": self.spid,
                "user_mobile": self.params["user_mobile"],
                "bank_valicode": "1234567", }
            query_params = self.cardpay_apply_md5(key, confirm_data)
            rsp = client.get('/cardpay/confirm?%s', query_string=query_params)

            assert rsp.status_code == 200
            json_rsp = json.loads(rsp.data)
            assert json_rsp["retcode"] == 0
            confirm_ret = util.rsa_decrypt(
                json_rsp['cipher_data'],
                config.TEST_MERCHANT_PRIVATE_KEY)
            listid = confirm_ret['list_id'][0]
            print(listid)

        # 查询接口
        qry_data = {
            "encode_type": "MD5",
            "list_id": list_id,
            "spid": self.spid,
            "channel": const.CHANNEL.API}

        query_params = self.cardpay_apply_md5(key, qry_data)
        rsp = client.get('/query/single', query_string=query_params)
        assert rsp.status_code == 200
        json_rsp = json.loads(rsp.data)
        assert json_resp["retcode"] == 0
        logger.debug(json_rsp)

    def test_cardpay_apply_rsa(self, client):
        u"""RSA签名 + RSA加密."""
        params = self.params

        # RSA签名 + RSA加密
        cipher_data = util.rsa_sign_and_encrypt_params(
            params,
            config.TEST_MERCHANT_PRIVATE_KEY,
            config.FENLE_PUB_KEY
        )

        query_params = {"cipher_data": cipher_data}
        resp = client.get('/cardpay/apply', query_string=query_params)

        assert resp.status_code == 200

        # json_resp = json.loads(resp.data)
        # assert json_resp["retcode"] == 0


def test_api_form_check_not_encrypted(db):
    app = Flask(__name__)
    app.config["TESTING"] = True

    # ############# 定义测试handler ###################
    @app.route("/test")
    @general("test")
    @api_form_check(
        {
            "spid": (10 <= F_str("商户号") <= 10) & "strict" & "required",
            "sign": (F_str("签名") <= 1024) & "strict" & "required",
            "encode_type": (F_str("") <= 5) & "strict" & "required" & (
                lambda v: (v in const.ENCODE_TYPE.ALL, v)),
        },
        is_encrypted=False
    )
    def test_handler(safe_vars):
        return "whatever"

    # ############# 参数错误 ###################
    resp = app.test_client().get('/test', query_string={"spid": "not exsit"})
    assert resp.status_code == 200
    json_resp = json.loads(resp.data)
    assert json_resp['retcode'] == const.API_ERROR.PARAM_ERROR

    merchant_data = {
        'spid': '1' * 10,
        'uid': '111',
        'mer_key': '654321' * 3,
        'agent_uid': '112',
        'parent_uid': '113',
        'status': 0,
        'sp_name': 'guazi',
        'rsa_pub_key': config.TEST_MERCHANT_PUB_KEY}
    ins = t_merchant_info.insert()
    db.execute(ins, merchant_data)

    # ############# 签名无效 ###################
    resp = app.test_client().get(
        '/test',
        query_string={
            "spid": '1' * 10,
            "encode_type": 'MD5',
            "sign": 'invalid',
        })
    assert resp.status_code == 200

    json_resp = json.loads(resp.data)
    assert json_resp['retcode'] == const.API_ERROR.SIGN_INVALID

    # ############# 签名有效 ###################
    raw_params = {
        "spid": '1' * 10,
        "encode_type": 'MD5',
    }
    params = [(k, v) for k, v in raw_params.items() if
              v is not None and v != ""]
    params = sorted(params, key=operator.itemgetter(0))
    params_with_key = params + [("key", "654321" * 3)]

    urlencoded_params = urllib.parse.urlencode(params_with_key)
    # MD5签名
    m = hashlib.md5()
    m.update(urlencoded_params.encode())
    sign = m.hexdigest()
    raw_params.update(sign=sign)
    resp = app.test_client().get(
        '/test',
        query_string=raw_params)
    assert resp.status_code == 200
    assert resp.data == b"whatever"


def test_api_form_check_trusted_ip(db):
    app = Flask(__name__)
    config.CLIENT_IP_WHITELIST = ("127.0.0.1", )

    # ############# 定义测试handler ###################
    @app.route("/test")
    @general("test")
    @api_form_check({
        "spid": (10 <= F_str("商户号") <= 10) & "strict" & "required"})
    def test_handler(safe_vars):
        return "whatever"

    merchant_data = {
        'spid': '1' * 10,
        'uid': '111',
        'mer_key': '654321' * 3,
        'agent_uid': '112',
        'parent_uid': '113',
        'status': 0,
        'sp_name': 'guazi',
        'rsa_pub_key': config.TEST_MERCHANT_PUB_KEY}
    ins = t_merchant_info.insert()
    db.execute(ins, merchant_data)

    resp = app.test_client().get(
        '/test', query_string={'spid': '1' * 10})
    assert resp.status_code == 200
    assert resp.data == b"whatever"


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

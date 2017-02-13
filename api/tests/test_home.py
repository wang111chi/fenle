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
from base.db import t_user_bank
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

    # 分配给商户的key, 用于MD5 签名
    key = "654321" * 3
    now = datetime.now()

    def init_balance(self, conn):
        """insert some test data to mysql table."""
        # initial sp_balance
        sp_balance_data = {
            'spid': self.spid,
            'cur_type': self.params['cur_type'],
            'uid': self.spid,
            'b_balance': 0,
            'modify_time': self.now,
            'create_time': self.now}
        conn.execute(t_sp_balance.insert(), sp_balance_data)
        # initial fenle_balance
        fenle_balance_data = {
            'account_no': config.FENLE_ACCOUNT_NO,
            'bank_type': config.FENLE_BANK_TYPE,
            'account_type': const.FENLE_ACCOUNT.VIRTUAL,
            'modify_time': self.now,
            'create_time': self.now}
        conn.execute(t_fenle_balance.insert(), fenle_balance_data)

    def insert_merchant(self, conn, status):
        # initial merchant_info
        merchant_data = {
            'spid': self.spid,
            'uid': '111',
            'mer_key': '654321' * 3,
            'agent_uid': '112',
            'parent_uid': '113',
            'status': status,
            'sp_name': 'guazi',
            'rsa_pub_key': config.TEST_MERCHANT_PUB_KEY}
        ins = t_merchant_info.insert()
        conn.execute(ins, merchant_data)

    def insert_channel(self, conn, valitype, is_enable):
        # initial bank_channel data
        bank_data = {
            'bank_channel': 1,
            'bank_type': self.bank_type,
            'is_enable': is_enable,
            # 修改此处决定是否验证手机号
            'bank_valitype': valitype,
            'fenqi_fee_percent': json.dumps({6: 300, 12: 400}),
            'rsp_time': 10,
            'settle_type': const.SETTLE_TYPE.DAY_SETTLE}
        conn.execute(t_bank_channel.insert(), bank_data)
        # return ret_channel._saved_cursor._last_insert_id

    def insert_user_bank(self, conn):
        # initial user_bank
        user_bank_info = {
            'account_no': self.params['user_account_no'],
            'account_type': self.params['user_account_type'],
            'bank_type': self.params['bank_type'],
            'account_mobile': self.params['user_mobile']}
        user_bank_info.update({
            'status': const.USER_BANK_STATUS.INIT,
            'lstate': const.LSTATE.HUNG,  # 设置为冻结标志
            'create_time': self.now,
            'modify_time': self.now})
        conn.execute(t_user_bank.insert(), user_bank_info)

    def insert_sp_bank(self, conn):
        # initial sp_bank data
        sp_bank_data = {
            'spid': self.spid,
            'bank_spid': self.spid + '12345',
            'bank_type': self.bank_type,
            'fenqi_fee_percent': json.dumps({6: 500, 12: 600}),
            'divided_term': '6,12',
            'settle_type': const.SETTLE_TYPE.DAY_SETTLE}
        conn.execute(t_sp_bank.insert(), sp_bank_data)

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

    def cardpay_apply(self, client, predict_ret):
        # @params<predict_ret>: 预计要返回的值
        query_params = self.cardpay_apply_md5(self.key, self.params)
        rsp = client.get('/cardpay/apply', query_string=query_params)
        assert rsp.status_code == 200
        json_rsp = json.loads(rsp.data)
        assert json_rsp["retcode"] == predict_ret
        if predict_ret == 0:
            params = util.rsa_decrypt(
                json_rsp['cipher_data'],
                config.TEST_MERCHANT_PRIVATE_KEY)
            return params['list_id'][0]

    def test_merchant_balance_check(self, client):
        self.cardpay_apply(client, const.API_ERROR.SP_BALANCE_NOT_EXIST)

    def test_merchant_check(self, client, db):
        self.init_balance(db)
        self.cardpay_apply(client, const.API_ERROR.SPID_NOT_EXIST)

    def test_merchant_forbid_check(self, client, db):
        self.init_balance(db)
        self.insert_merchant(db, const.MERCHANT_STATUS.FORBID)
        self.cardpay_apply(client, const.API_ERROR.MERCHANT_FORBID)

    def test_channel_check(self, client, db):
        self.init_balance(db)
        self.insert_merchant(db, const.MERCHANT_STATUS.OPEN)
        self.cardpay_apply(client, const.API_ERROR.BANK_NOT_EXIST)

    def test_channel_unable_check(self, client, db):
        self.init_balance(db)
        self.insert_merchant(db, const.MERCHANT_STATUS.OPEN)
        self.insert_channel(
            db, const.BANK_VALITYPE.MOBILE_NOT_VALID,
            const.BOOLEAN.FALSE)
        self.cardpay_apply(client, const.API_ERROR.BANK_CHANNEL_UNABLE)

    def test_userbank_check(self, client, db):
        self.init_balance(db)
        self.insert_merchant(db, const.MERCHANT_STATUS.OPEN)
        self.insert_channel(
            db, const.BANK_VALITYPE.MOBILE_VALID,
            const.BOOLEAN.FALSE)
        self.insert_user_bank(db)
        self.cardpay_apply(client, const.API_ERROR.ACCOUNT_FREEZED)

    def test_cardpay_apply_md5(self, client, db):
        self.insert_merchant(db, const.MERCHANT_STATUS.OPEN)
        self.insert_sp_bank(db)
        self.insert_channel(
            db, const.BANK_VALITYPE.MOBILE_NOT_VALID,
            const.BOOLEAN.TRUE)
        self.init_balance(db)

        # 测试不验证手机号的支付请求
        list_id = self.cardpay_apply(client, const.REQUEST_STATUS.SUCCESS)
        # 测试重复调用的反应
        list_ids = self.cardpay_apply(client, const.REQUEST_STATUS.SUCCESS)
        assert list_id == list_ids

    """
    def check_merchant(self, client, db):
        self.insert_merchant(db)
        self.insert_channel(db, const.BANK_VALITYPE.MOBILE_NOT_VALID)
        self.insert_sp_bank(db)
        self.init_balance(db)
    """

    def test_cardpay_confirm_md5(self, client, db):
        self.insert_merchant(db, const.MERCHANT_STATUS.OPEN)
        self.insert_sp_bank(db)
        self.insert_channel(
            db, const.BANK_VALITYPE.MOBILE_VALID,
            const.BOOLEAN.TRUE)
        self.init_balance(db)

        # 测试验证手机号的支付请求
        list_id = self.cardpay_apply(client, const.REQUEST_STATUS.SUCCESS)

        # 测试支付确认
        confirm_data = {
            "encode_type": "MD5",
            "list_id": list_id,
            "spid": self.spid,
            "sp_tid": self.params["sp_tid"],
            "user_mobile": self.params["user_mobile"],
            "user_account_no": self.params["user_account_no"],
            "bank_valicode": "1234567", }
        query_params = self.cardpay_apply_md5(self.key, confirm_data)
        confirm_rsp = client.get(
            '/cardpay/confirm', query_string=query_params)
        assert confirm_rsp.status_code == 200
        json_confirm_rsp = json.loads(confirm_rsp.data)
        assert json_confirm_rsp["retcode"] == 0
        confirm_ret = util.rsa_decrypt(
            json_confirm_rsp['cipher_data'],
            config.TEST_MERCHANT_PRIVATE_KEY)
        list_id = confirm_ret['list_id'][0]

        # 测试正确的查询
        qry_data = {
            "encode_type": "MD5",
            "list_id": list_id,
            "spid": self.spid,
            "channel": const.CHANNEL.API}

        query_params = self.cardpay_apply_md5(self.key, qry_data)
        qry_rsp = client.get(
            '/cardpay/query', query_string=query_params)
        assert qry_rsp.status_code == 200
        json_qry_rsp = json.loads(qry_rsp.data)
        assert json_qry_rsp["retcode"] == 0
        params = util.rsa_decrypt(
            json_qry_rsp['cipher_data'],
            config.TEST_MERCHANT_PRIVATE_KEY)
        logger.debug(params)

        # 测试错误spid的查询
        qry_data.update({'spid': '65' * 5})  # 将spid改为错误的
        query_params = self.cardpay_apply_md5(self.key, qry_data)
        spid_qry = client.get(
            '/cardpay/query', query_string=query_params)
        assert spid_qry.status_code == 200
        json_spid_qry = json.loads(spid_qry.data)
        assert json_spid_qry["retcode"] == const.API_ERROR.SPID_NOT_EXIST

    def test_single_query(self, client):
        """测试错误的查询"""
        qry_data = {
            "encode_type": "MD5",
            "list_id": "543223",  # 给一个不存在的list_id
            "spid": self.spid,
            "channel": const.CHANNEL.API}

        query_params = self.cardpay_apply_md5(self.key, qry_data)
        rsp = client.get('/cardpay/query', query_string=query_params)
        assert rsp.status_code == 200
        json_rsp = json.loads(rsp.data)
        assert json_rsp["retcode"] == const.API_ERROR.LIST_ID_NOT_EXIST

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

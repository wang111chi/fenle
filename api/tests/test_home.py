#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import operator
import hashlib
from base64 import b64encode
from base64 import b64decode
import json
from unittest import mock

import datetime
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
from base.db import t_trans_list
import config
from base import logger
from base import constant as const
from base.framework import ApiJsonErrorResponse
from base.framework import general, api_form_check
from base.xform import F_str
from base import dblogic as dbl


class SpModel():
    """商户端模型"""

    # 测试参数模板
    now = datetime.datetime.now()
    spid = '1' * 10
    sp_private_key = config.TEST_MERCHANT_PRIVATE_KEY
    params = {
        "encode_type": "MD5",
        "spid": spid,
        "sp_list": "1234567",
        "true_name": u"张三",
        "pin_code": "9376",
        "memo": u"测试商品",
        "attach": "wang",
        "cur_type": const.CUR_TYPE.RMB,
        "account_type": 0,
        "bank_type": 1001,
        "amount": 12345,
        "bankacc_no": "1234567890123456",
        "mobile": "13312345678",
        "valid_date": "2020-05",
        "bank_sms_time": now,
        "bank_validcode": "456789"
    }

    # 分配给商户的key, 用于MD5 签名
    key = "654321" * 3
    fee_duty = 1

    def insert_merchant(self, conn, spid, status):
        merchant_data = {
            'spid': spid,
            'sp_name': 'yidong',
            'mer_key': self.key,
            'status': status,
            'rsa_pub_key': config.TEST_MERCHANT_PUB_KEY}
        conn.execute(t_merchant_info.insert(), merchant_data)

    def insert_balance(self, conn):
        """insert some test data to mysql table."""
        # initial sp_balance B account
        sp_balance_data = {
            'spid': self.spid,
            'account_class': const.ACCOUNT_CLASS.B,
            'balance': 0,
            'freezing': 0,
            'modify_time': self.now,
            'create_time': self.now}
        conn.execute(t_sp_balance.insert(), sp_balance_data)
        # initial sp_balance C account
        sp_balance_data.update({
            'account_class': const.ACCOUNT_CLASS.C})
        conn.execute(t_sp_balance.insert(), sp_balance_data)
        # initial fenle C account
        sp_balance_data.update({
            'spid': config.FENLE_SPID})
        conn.execute(t_sp_balance.insert(), sp_balance_data)
        # initial fenle_balance
        fenle_balance_data = {
            'bankacc_no': config.FENLE_ACCOUNT_NO,
            'account_type': const.FENLE_ACCOUNT.VIRTUAL,
            'bank_type': config.FENLE_BANK_TYPE,
            'balance': 0,
            'modify_time': self.now,
            'create_time': self.now}
        conn.execute(t_fenle_balance.insert(), fenle_balance_data)

    def insert_user_bank(self, conn):
        user_bank_info = {
            'bankacc_no': self.params['bankacc_no'],
            'account_type': self.params['account_type'],
            'bank_type': self.params['bank_type'],
            'account_mobile': self.params['mobile'],
            'status': const.USER_BANK_STATUS.FREEZING,
            'create_time': self.now,
            'modify_time': self.now}
        conn.execute(t_user_bank.insert(), user_bank_info)

    def insert_channel(self, conn, is_enable, fee_percent_json, vmask=0):
        bank_data = {
            'bank_type': self.params['bank_type'],
            'bank_valitype': const.BANK_VALITYPE.MOBILE_VALID,  # 修改此处决定是否验证手机号
            'interface_mask': vmask,
            'fenqi_fee_percent': json.dumps(fee_percent_json),
            'jifen_fee_percent': 0,
            'cash_fee_percent': 200,
            'settle_type': const.SETTLE_TYPE.DAY_SETTLE,
            'status': is_enable,
            'create_time': self.now,
            'modify_time': self.now
        }
        conn.execute(t_bank_channel.insert(), bank_data)

    def insert_sp_bank(self, conn, spid, fee_percent_json):
        sp_bank_data = {
            'spid': spid,
            'bank_spid': spid[0:7],
            'terminal_no': spid[7:],
            'bank_type': self.params['bank_type'],
            'fenqi_fee_percent': json.dumps(fee_percent_json),
            'jifen_fee_percent': 300,
            'cash_fee_percent': 300,
            'settle_type': const.SETTLE_TYPE.DAY_SETTLE,
            'create_time': self.now,
            'modify_time': self.now
        }
        conn.execute(t_sp_bank.insert(), sp_bank_data)

    def sign_encrypt_md5(self, key, params):
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


class TestSms(SpModel):
    def sms_send(self, client, predict_ret):
        sms_data = dict((k, self.params[k]) for k in (
            'encode_type', 'spid', 'true_name', 'pin_code',
            'bank_type', 'amount', 'bankacc_no', 'mobile', 'valid_date'))

        query_params = self.sign_encrypt_md5(self.key, sms_data)
        sms_rsp = client.get(
            '/sms/send', query_string=query_params)
        assert sms_rsp.status_code == 200
        json_sms_rsp = json.loads(sms_rsp.data)
        assert json_sms_rsp["retcode"] == predict_ret
        if predict_ret == 0:
            sms_ret = util.rsa_decrypt(
                json_sms_rsp['cipher_data'],
                config.TEST_MERCHANT_PRIVATE_KEY)
            return sms_ret

    def test_sms_spid_check(self, client, db):
        self.insert_merchant(db, '34' * 5, const.MERCHANT_STATUS.OPEN)
        self.sms_send(client, const.API_ERROR.SPID_NOT_EXIST)

    def test_sms_merchant_check(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.FORBID)
        self.sms_send(client, const.API_ERROR.MERCHANT_FORBID)

    def test_sms_usrbank_check(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_user_bank(db)
        self.sms_send(client, const.API_ERROR.ACCOUNT_FREEZED)

    def test_sms_bank_check(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.sms_send(client, const.API_ERROR.BANK_NOT_EXIST)

    def test_sms_channel_check(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.FALSE, {6: 500, 12: 600})
        self.sms_send(client, const.API_ERROR.BANK_CHANNEL_UNABLE)

    def test_sms_spbank_check(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {6: 500, 12: 600})
        self.insert_sp_bank(db, '57' * 5, {6: 500, 12: 600})
        self.sms_send(client, const.API_ERROR.NO_SP_BANK)

    def test_sms_banksys_ok(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {6: 500, 12: 600})
        self.insert_sp_bank(db, self.spid, {6: 500, 12: 600})
        with mock.patch("base.pp_interface.call2") as cd:
            cd.return_value = (True, {
                "bank_sms_time": self.now.strftime("%m%d")})
            self.sms_send(client, const.REQUEST_STATUS.SUCCESS)

    def test_sms_banksys_err(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {6: 500, 12: 600})
        self.insert_sp_bank(db, self.spid, {6: 500, 12: 600})
        with mock.patch("base.pp_interface.call2") as cd:
            cd.return_value = (False, const.API_ERROR.BANK_ERROR)
            self.sms_send(client, const.API_ERROR.BANK_ERROR)


class Trans(SpModel):
    params = {'div_term': 6}
    params.update(SpModel.params)

    def layaway_trade(self, client, params, predict_ret):
        query_params = self.sign_encrypt_md5(self.key, params)
        rsp = client.get('/layaway/trade', query_string=query_params)
        assert rsp.status_code == 200
        json_rsp = json.loads(rsp.data)
        assert json_rsp["retcode"] == predict_ret
        if predict_ret == 0:
            params = util.rsa_decrypt(
                json_rsp['cipher_data'],
                config.TEST_MERCHANT_PRIVATE_KEY)
            return params['id'][0]

    def test_trade_spid_check(self, client, db):
        self.insert_merchant(db, '23' * 5, const.MERCHANT_STATUS.OPEN)
        self.layaway_trade(
            client, self.params, const.API_ERROR.SPID_NOT_EXIST)

    def test_trade_merchant_check(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.FORBID)
        self.layaway_trade(
            client, self.params, const.API_ERROR.MERCHANT_FORBID)

    def test_trade_userbank_check(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_user_bank(db)
        self.layaway_trade(
            client, self.params, const.API_ERROR.ACCOUNT_FREEZED)

    def test_trade_bank_check(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.layaway_trade(
            client, self.params, const.API_ERROR.BANK_NOT_EXIST)

    def test_trade_channel_check(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.FALSE, {6: 500, 12: 600})
        self.layaway_trade(
            client, self.params, const.API_ERROR.BANK_CHANNEL_UNABLE)

    def test_trade_channel_div_check(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {8: 500, 12: 600})
        self.layaway_trade(
            client, self.params, const.API_ERROR.DIV_TERM_NOT_EXIST)

    def test_trade_channel_pin_check(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {6: 500, 12: 600},
                            const.PAY_MASK.PIN_CODE)
        param = self.params.copy()
        param.pop('pin_code', None)
        self.layaway_trade(
            client, param, const.API_ERROR.NO_PIN_CODE)

    def test_trade_channel_name_check(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {6: 500, 12: 600},
                            const.PAY_MASK.NAME)
        param = self.params.copy()
        param.pop('true_name', None)
        self.layaway_trade(
            client, param, const.API_ERROR.NO_USER_NAME)

    def test_trade_spbank_spid_check(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {6: 500, 12: 600})
        self.insert_sp_bank(db, '57' * 5, {6: 500, 12: 600})
        self.layaway_trade(
            client, self.params, const.API_ERROR.NO_SP_BANK)

    def test_trade_spbank_div_check(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {6: 500, 12: 600})
        self.insert_sp_bank(db, self.spid, {8: 500, 12: 600})
        param = self.params.copy()
        self.layaway_trade(
            client, param, const.API_ERROR.DIV_TERM_NOT_EXIST)

    def test_trade_banksys_err(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {6: 500, 12: 600})
        self.insert_sp_bank(db, self.spid, {6: 500, 12: 600})
        with mock.patch("base.pp_interface.call2") as cd:
            cd.return_value = (False, None)
            self.layaway_trade(
                client, self.params, const.API_ERROR.BANK_ERROR)

    def test_trade_banksys_ok(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {6: 500, 12: 600})
        self.insert_sp_bank(db, self.spid, {6: 500, 12: 600})
        with mock.patch("base.pp_interface.call2") as cd:
            cd.return_value = (True, {
                "bank_roll": '5432109876',
                "bank_settle_time": self.now.strftime("%m%d")})
            self.layaway_trade(
                client, self.params, const.REQUEST_STATUS.SUCCESS)

    def test_trade_repeat(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {6: 500, 12: 600})
        self.insert_sp_bank(db, self.spid, {6: 500, 12: 600})
        with mock.patch("base.pp_interface.call2") as cd:
            cd.return_value = (True, {
                "bank_roll": '5432109876',
                "bank_settle_time": self.now.strftime("%m%d")})
            self.layaway_trade(
                client, self.params, const.REQUEST_STATUS.SUCCESS)
        # 测试重复调用的反应
        param = self.params.copy()
        param['mobile'] = '11100000000'
        self.layaway_trade(
            client, param, const.API_ERROR.REPEAT_PAY_MOBILE_ERROR)
        param['mobile'] = self.params['mobile']
        param['bankacc_no'] = '1' * 16
        self.layaway_trade(
            client, param, const.API_ERROR.REPEAT_PAY_ACCOUNTNO_ERROR)
        param['bankacc_no'] = self.params['bankacc_no']
        param['amount'] = 11111
        self.layaway_trade(
            client, param, const.API_ERROR.REPEAT_PAY_AMOUNT_ERROR)
        param['amount'] = self.params['amount']
        param['bank_type'] = 1000
        self.layaway_trade(
            client, param, const.API_ERROR.REPEAT_PAY_BANKTYPE_ERROR)
        self.layaway_trade(
            client, self.params, const.REQUEST_STATUS.SUCCESS)


class TestRefund_TransQuery(Trans):
    def trans_query(self, client, list_id, predict_ret):
        query_param = {"encode_type": "MD5",
                       "spid": self.params['spid'],
                       "list_id": list_id}
        query_params = self.sign_encrypt_md5(
            self.key, query_param)
        rsp = client.get('/trans/query', query_string=query_params)
        assert rsp.status_code == 200
        json_rsp = json.loads(rsp.data)
        assert json_rsp["retcode"] == predict_ret
        if predict_ret == 0:
            params = util.rsa_decrypt(
                json_rsp['cipher_data'],
                config.TEST_MERCHANT_PRIVATE_KEY)
            return params

    def test_query_banklist_err(self, client):
        return self.trans_query(
            client, '1' * 10, const.API_ERROR.LIST_ID_NOT_EXIST)

    def test_query(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {6: 500, 12: 600})
        self.insert_sp_bank(db, self.spid, {6: 500, 12: 600})
        params = self.params.copy()
        with mock.patch("base.pp_interface.call2") as cd:
            cd.return_value = (True, {
                "bank_roll": '5432109876',
                "bank_settle_time": self.now.strftime("%m%d")})
            list_id = self.layaway_trade(
                client, params, const.REQUEST_STATUS.SUCCESS)
        return self.trans_query(
            client, list_id, const.REQUEST_STATUS.SUCCESS)

    def refund(self, client, list_id, predict_ret):
        query_param = {"encode_type": "MD5",
                       "spid": self.params['spid'],
                       "sp_refund_id": list_id,
                       "list_id": list_id}
        query_params = self.sign_encrypt_md5(
            self.key, query_param)
        rsp = client.get('/trans/refund', query_string=query_params)
        assert rsp.status_code == 200
        json_rsp = json.loads(rsp.data)
        assert json_rsp["retcode"] == predict_ret
        if predict_ret == 0:
            params = util.rsa_decrypt(
                json_rsp['cipher_data'],
                config.TEST_MERCHANT_PRIVATE_KEY)
            return params['result'][0]

    def test_refund_spid(self, client, db):
        self.refund(client, '543212345', const.API_ERROR.SPID_NOT_EXIST)

    def test_refund_sp(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.FORBID)
        self.refund(client, '543212345', const.API_ERROR.MERCHANT_FORBID)

    def test_refund_list(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.refund(client, '543212345', const.API_ERROR.LIST_ID_NOT_EXIST)

    def test_refund_time(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {6: 500, 12: 600})
        self.insert_sp_bank(db, self.spid, {6: 500, 12: 600})
        params = self.params.copy()
        with mock.patch("base.pp_interface.call2") as cd:
            cd.return_value = (True, {
                "bank_roll": '5432109876',
                "bank_settle_time":
                    (self.now + datetime.timedelta(days=32)).strftime("%m%d")})
            list_id = self.layaway_trade(
                client, params, const.REQUEST_STATUS.SUCCESS)
        self.refund(
            client, list_id, const.API_ERROR.REFUND_TIME_OVER)

    def test_refund_theday_ok(self, client, db):
        self.insert_merchant(db, self. spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {6: 500, 12: 600})
        self.insert_sp_bank(db, self.spid, {6: 500, 12: 600})
        params = self.params.copy()
        with mock.patch("base.pp_interface.call2") as cd:
            cd.return_value = (True, {
                "bank_roll": '5432109876',
                "bank_settle_time": self.now.strftime("%m%d")})
            list_id = self.layaway_trade(
                client, params, const.REQUEST_STATUS.SUCCESS)
            self.refund(client, list_id, const.REQUEST_STATUS.SUCCESS)

    def test_refund_theday_err(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {6: 500, 12: 600})
        self.insert_sp_bank(db, self.spid, {6: 500, 12: 600})
        params = self.params.copy()
        with mock.patch("base.pp_interface.call2") as cd:
            cd.return_value = (True, {
                "bank_roll": '5432109876',
                "bank_settle_time": self.now.strftime("%m%d")})
            list_id = self.layaway_trade(
                client, params, const.REQUEST_STATUS.SUCCESS)
        with mock.patch("base.pp_interface.call2") as cd:
            cd.return_value = (False, const.API_ERROR.BANK_ERROR)
            self.refund(client, list_id, const.API_ERROR.BANK_ERROR)

    def test_refund_bank_settled(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {6: 500, 12: 600})
        self.insert_sp_bank(db, self.spid, {6: 500, 12: 600})
        params = self.params.copy()
        with mock.patch("base.pp_interface.call2") as cd:
            cd.return_value = (True, {
                "bank_roll": '5432109876',
                "bank_settle_time": self.now.strftime("%m%d")})
            list_id = self.layaway_trade(
                client, params, const.REQUEST_STATUS.SUCCESS)

        target = self.now + datetime.timedelta(days=1)
        with mock.patch.object(datetime, 'datetime', mock.Mock(
                wraps=datetime.datetime)) as patched:
            patched.now.return_value = target
            self.refund(
                client, list_id, const.REQUEST_STATUS.SUCCESS)

    def test_refund_before_c2b_ok(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {6: 500, 12: 600})
        self.insert_sp_bank(db, self.spid, {6: 500, 12: 600})
        params = self.params.copy()
        with mock.patch("base.pp_interface.call2") as cd:
            cd.return_value = (True, {
                "bank_roll": '5432109876',
                "bank_settle_time": self.now.strftime("%m%d")})
            list_id = self.layaway_trade(
                client, params, const.REQUEST_STATUS.SUCCESS)

        db.execute(t_trans_list.update().where(
            t_trans_list.c.id == list_id).values(
                settle_time=self.now, modify_time=self.now))
        target = self.now + datetime.timedelta(days=1)
        with mock.patch.object(datetime, 'datetime', mock.Mock(
                wraps=datetime.datetime)) as patched:
            patched.now.return_value = target
            with mock.patch("base.pp_interface.call2") as cd:
                cd.return_value = (True, {
                    "bank_roll": '5432109876',
                    "bank_settle_time": self.now.strftime("%m%d")})
                self.refund(client, list_id, const.REQUEST_STATUS.SUCCESS)

    def test_refund_before_c2b_err(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {6: 500, 12: 600})
        self.insert_sp_bank(db, self.spid, {6: 500, 12: 600})
        params = self.params.copy()
        with mock.patch("base.pp_interface.call2") as cd:
            cd.return_value = (True, {
                "bank_roll": '5432109876',
                "bank_settle_time": self.now.strftime("%m%d")})
            list_id = self.layaway_trade(
                client, params, const.REQUEST_STATUS.SUCCESS)

        db.execute(t_trans_list.update().where(
            t_trans_list.c.id == list_id).values(
                settle_time=self.now, modify_time=self.now))
        target = self.now + datetime.timedelta(days=1)
        with mock.patch.object(datetime, 'datetime', mock.Mock(
                wraps=datetime.datetime)) as patched:
            patched.now.return_value = target
            with mock.patch("base.pp_interface.call2") as cd:
                cd.return_value = (False, const.API_ERROR.BANK_ERROR)
                self.refund(client, list_id, const.API_ERROR.BANK_ERROR)

    def test_refund_after_c2b_ok(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {6: 500, 12: 600})
        self.insert_sp_bank(db, self.spid, {6: 500, 12: 600})
        params = self.params.copy()
        with mock.patch("base.pp_interface.call2") as cd:
            cd.return_value = (True, {
                "bank_roll": '5432109876',
                "bank_settle_time": self.now.strftime("%m%d")})
            list_id = self.layaway_trade(
                client, params, const.REQUEST_STATUS.SUCCESS)

        a_list = dbl.get_list(db, list_id)
        dbl.settle_a_list(db, a_list, self.now)
        target = self.now + datetime.timedelta(days=1)
        with mock.patch.object(datetime, 'datetime', mock.Mock(
                wraps=datetime.datetime)) as patched:
            patched.now.return_value = target
            with mock.patch("base.pp_interface.call2") as cd:
                cd.return_value = (True, {
                    "bank_roll": '5432109876',
                    "bank_settle_time": self.now.strftime("%m%d")})
                self.refund(client, list_id, const.REQUEST_STATUS.SUCCESS)

    def test_refund_after_c2b_err(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {6: 500, 12: 600})
        self.insert_sp_bank(db, self.spid, {6: 500, 12: 600})
        params = self.params.copy()
        with mock.patch("base.pp_interface.call2") as cd:
            cd.return_value = (True, {
                "bank_roll": '5432109876',
                "bank_settle_time": self.now.strftime("%m%d")})
            list_id = self.layaway_trade(
                client, params, const.REQUEST_STATUS.SUCCESS)

        a_list = dbl.get_list(db, list_id)
        dbl.settle_a_list(db, a_list, self.now)
        target = self.now + datetime.timedelta(days=1)
        with mock.patch.object(datetime, 'datetime', mock.Mock(
                wraps=datetime.datetime)) as patched:
            patched.now.return_value = target
            with mock.patch("base.pp_interface.call2") as cd:
                cd.return_value = (False, const.API_ERROR.BANK_ERROR)
                self.refund(client, list_id, const.API_ERROR.BANK_ERROR)

    def test_refund_withdraw(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {6: 500, 12: 600})
        self.insert_sp_bank(db, self.spid, {6: 500, 12: 600})
        params = self.params.copy()
        with mock.patch("base.pp_interface.call2") as cd:
            cd.return_value = (True, {
                "bank_roll": '5432109876',
                "bank_settle_time": self.now.strftime("%m%d")})
            list_id = self.layaway_trade(
                client, params, const.REQUEST_STATUS.SUCCESS)

        a_list = dbl.get_list(db, list_id)
        dbl.settle_a_list(db, a_list, self.now)
        dbl.with_draw(db, a_list['spid'], a_list['amount'] / 3, self.now)
        target = self.now + datetime.timedelta(days=1)
        with mock.patch.object(datetime, 'datetime', mock.Mock(
                wraps=datetime.datetime)) as patched:
            patched.now.return_value = target
            self.refund(client, list_id, const.API_ERROR.REFUND_LESS_BALANCE)


class TestPointCash(SpModel):
    params = {'jf_deduct_money': 3000}
    params.update(SpModel.params)

    def point_cash(self, client, params, predict_ret):
        query_params = self.sign_encrypt_md5(self.key, params)
        rsp = client.get('/point_cash/trade', query_string=query_params)
        assert rsp.status_code == 200
        json_rsp = json.loads(rsp.data)
        assert json_rsp["retcode"] == predict_ret
        if predict_ret == 0:
            params = util.rsa_decrypt(
                json_rsp['cipher_data'],
                config.TEST_MERCHANT_PRIVATE_KEY)
            return params['id'][0]

    def test_pointcash_banksys_err(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {6: 500, 12: 600})
        self.insert_sp_bank(db, self.spid, {6: 500, 12: 600})
        with mock.patch("base.pp_interface.call2") as cd:
            cd.return_value = (False, None)
            self.point_cash(
                client, self.params, const.API_ERROR.BANK_ERROR)

    def test_pointcash_banksys_ok(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {6: 500, 12: 600})
        self.insert_sp_bank(db, self.spid, {6: 500, 12: 600})
        with mock.patch("base.pp_interface.call2") as cd:
            cd.return_value = (True, {
                "bank_roll": '5432109876',
                "bank_settle_time": self.now.strftime("%m%d")})
            self.point_cash(
                client, self.params, const.REQUEST_STATUS.SUCCESS)


class TestConsume(SpModel):
    def consume(self, client, params, predict_ret):
        query_params = self.sign_encrypt_md5(self.key, params)
        rsp = client.get('/consume/trade', query_string=query_params)
        assert rsp.status_code == 200
        json_rsp = json.loads(rsp.data)
        assert json_rsp["retcode"] == predict_ret
        if predict_ret == 0:
            params = util.rsa_decrypt(
                json_rsp['cipher_data'],
                config.TEST_MERCHANT_PRIVATE_KEY)
            return params['id'][0]

    def test_consume_banksys_err(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {6: 500, 12: 600})
        self.insert_sp_bank(db, self.spid, {6: 500, 12: 600})
        with mock.patch("base.pp_interface.call2") as cd:
            cd.return_value = (False, None)
            self.consume(
                client, self.params, const.API_ERROR.BANK_ERROR)

    def test_consume_banksys_ok(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {6: 500, 12: 600})
        self.insert_sp_bank(db, self.spid, {6: 500, 12: 600})
        with mock.patch("base.pp_interface.call2") as cd:
            cd.return_value = (True, {
                "bank_roll": '5432109876',
                "bank_settle_time": self.now.strftime("%m%d")})
            self.consume(
                client, self.params, const.REQUEST_STATUS.SUCCESS)


class TestPoint(SpModel):
    def point(self, client, params, predict_ret):
        query_params = self.sign_encrypt_md5(self.key, params)
        rsp = client.get('/point/trade', query_string=query_params)
        assert rsp.status_code == 200
        json_rsp = json.loads(rsp.data)
        assert json_rsp["retcode"] == predict_ret
        if predict_ret == 0:
            params = util.rsa_decrypt(
                json_rsp['cipher_data'],
                config.TEST_MERCHANT_PRIVATE_KEY)
            return params['id'][0]

    def test_point_banksys_err(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {6: 500, 12: 600})
        self.insert_sp_bank(db, self.spid, {6: 500, 12: 600})
        with mock.patch("base.pp_interface.call2") as cd:
            cd.return_value = (False, None)
            self.point(
                client, self.params, const.API_ERROR.BANK_ERROR)

    def test_point_banksys_ok(self, client, db):
        self.insert_merchant(db, self.spid, const.MERCHANT_STATUS.OPEN)
        self.insert_balance(db)
        self.insert_channel(db, const.BOOLEAN.TRUE, {6: 500, 12: 600})
        self.insert_sp_bank(db, self.spid, {6: 500, 12: 600})
        with mock.patch("base.pp_interface.call2") as cd:
            cd.return_value = (True, {
                "bank_roll": '5432109876',
                "bank_settle_time": self.now.strftime("%m%d")})
            self.point(
                client, self.params, const.REQUEST_STATUS.SUCCESS)
    """
    def test_point_query(self, client):
        query_param = dict((k, self.params[k]) for k in (
            'bankacc_no', 'mobile', 'valid_date',
            'bank_sms_time', 'bank_validcode'))
    """


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
        'spid': '2' * 10,
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
            "spid": '2' * 10,
            "encode_type": 'MD5',
            "sign": 'invalid',
        })
    assert resp.status_code == 200

    json_resp = json.loads(resp.data)
    assert json_resp['retcode'] == const.API_ERROR.SIGN_INVALID

    # ############# 签名有效 ###################
    raw_params = {
        "spid": '2' * 10,
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
        'spid': '2' * 10,
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
        '/test', query_string={'spid': '2' * 10})
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

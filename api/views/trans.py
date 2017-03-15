#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base64 import b64decode
import operator
import hashlib
import urllib
import datetime
import json
from itertools import chain

from flask import Blueprint, request
from sqlalchemy.sql import text, select, and_, or_
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Signature import PKCS1_v1_5 as sign_PKCS1_v1_5
from Crypto.Hash import SHA

from base import pp_interface as pi
from base.framework import db_conn, general
from base.framework import api_form_check
from base.framework import ApiJsonErrorResponse, ApiJsonOkResponse
from base.framework import TempResponse, transaction
from base.xform import F_mobile, F_str, F_int, F_datetime
from base import constant as const
from base import dblogic as dbl
from base import util
from base.db import t_sp_balance
from base.db import t_sp_history
from base.db import t_fenle_balance
from base.db import t_fenle_history
from base.db import t_refund_list
from base.db import t_trans_list

import config


trans = Blueprint("trans", __name__)


@trans.route("/trans/query")
@general("单笔查询接口")
@db_conn
@api_form_check({
    "sign": (F_str("签名") <= 1024) & "strict" & "required",
    "encode_type": (F_str("") <= 5) & "strict" & "required" & (
        lambda v: (v in const.ENCODE_TYPE.ALL, v)),
    "spid": (10 <= F_str("商户号") <= 10) & "strict" & "required",
    "bank_list": F_str("给银行订单号") & "strict" & "required",
})
def trans_query(db, safe_vars):
    ok, list_msg = dbl.get_list(db, safe_vars['bank_list'])
    if not ok:
        return ApiJsonErrorResponse(list_msg)
    list_data = dict(list_msg)
    sp_pubkey = dbl.get_sp_pubkey(db, list_msg['spid'])
    # 返回的参数
    ret_data = {'bank_list': safe_vars['bank_list'],
                'encode_type': const.ENCODE_TYPE.RSA}
    for k in ('spid', 'sp_list', 'amount', 'cur_type',
              'div_term', 'fee_duty'):
        ret_data[k] = list_data.get(k)

    cipher_data = util.rsa_sign_and_encrypt_params(
        ret_data, config.FENLE_PRIVATE_KEY, sp_pubkey)
    return ApiJsonOkResponse(cipher_data=cipher_data)


@trans.route("/trans/refund")
@general("退款接口")
@db_conn
@api_form_check({
    "sign": (F_str("签名") <= 1024) & "strict" & "required",
    "encode_type": (F_str("") <= 5) & "strict" & "required" & (
        lambda v: (v in const.ENCODE_TYPE.ALL, v)),
    "spid": (10 <= F_str("商户号") <= 10) & "strict" & "required",
    "bank_list": F_str("给银行订单号") & "strict" & "required",
})
def refund(db, safe_vars):
    ok, msg = _cancel_or_refund(db, safe_vars["bank_list"])
    if not ok:
        return ApiJsonErrorResponse(msg)
    sp_pubkey = dbl.get_sp_pubkey(db, safe_vars['spid'])
    cipher_data = util.rsa_sign_and_encrypt_params(
        msg, config.FENLE_PRIVATE_KEY, sp_pubkey)
    return ApiJsonOkResponse(cipher_data=cipher_data)


def _cancel_or_refund(db, bank_list):
    is_ok, list_ret = dbl.get_list(
        db, bank_list, const.TRANS_STATUS.PAY_SUCCESS)
    if not is_ok:
        return False, list_ret

    now = datetime.datetime.now()
    bank_settle_time = list_ret['bank_settle_time']
    create_time = list_ret['create_time']
    if bank_settle_time[0:2] == '12' and create_time.month == 1:
        bank_settle_time = datetime.datetime.strptime(
            str(create_time.year - 1) + bank_settle_time, "%Y%m%d")
    elif bank_settle_time[0:2] == '01' and create_time.month == 12:
        bank_settle_time = datetime.datetime.strptime(
            str(create_time.year + 1) + bank_settle_time, "%Y%m%d")
    else:
        bank_settle_time = datetime.datetime.strptime(
            str(create_time.year) + bank_settle_time, "%Y%m%d")

    if abs((bank_settle_time - create_time).days) > 30:
        return False, const.API_ERROR.REFUND_TIME_OVER

    # 退款单号
    refund_id = util.gen_refund_id(
        list_ret['spid'], list_ret['bank_type'])
    refund_data = {
        'id': refund_id,
        'spid': list_ret['spid'],
        'list_id': list_ret['id'],
        'create_time': now,
        'modify_time': now,
        'status': const.REFUND_STATUS.REFUNDING}
    db.execute(t_refund_list.insert(), refund_data)

    def gen_sp_history_data(spid, amount, now, account_class):
        return {'biz': const.BIZ.REFUND,
                'amount': amount,
                'ref_str_id': refund_id,  # 退款单号
                'create_time': now,
                'account_class': account_class,
                'spid': spid}

    def gen_fenle_history_data(amount, now):
        return {'biz': const.BIZ.REFUND,
                'amount': amount,
                'ref_str_id': refund_id,  # 退款单号
                'create_time': now,
                'bankacc_no': config.FENLE_ACCOUNT_NO,
                'bank_type': config.FENLE_BANK_TYPE}

    def gen_ret_data(status, modify_time):
        """返回的数据"""
        return {'spid': list_ret['spid'],
                'refund_id': refund_id,
                'amount': list_ret['amount'],
                'list_id': list_ret['id'],
                'result': status,
                'modify_time': modify_time}

    def call_interface(is_settled):
        terminal_no, bank_spid = dbl.get_terminal_spid(
            db, list_ret['spid'], list_ret['bank_type'])
        interface_input = {
            "ver": "1.0",
            "request_type":
                const.PRODUCT.REFUND_REQUEST_TYPE[list_ret["product"]] if
                is_settled else
                const.PRODUCT.CANCEL_REQUEST_TYPE[list_ret["product"]],
            'terminal_no': terminal_no,
            'bank_spid': bank_spid,
            'bank_list': bank_list}
        for k in ("bank_type", "valid_date", "bankacc_no", "amount",
                  "jf_deduct_money", "bank_roll", "bank_settle_time"):
            interface_input[k] = list_ret[k]
        return pi.call2(interface_input)

    if now.date() == bank_settle_time.date():
        # 调用银行撤销接口
        ok, msg = call_interface(is_settled=False)
        now2 = datetime.datetime.now()
        if not ok:
            db.execute(t_refund_list.update().where(
                t_refund_list.c.id == refund_id).values(
                status=const.REFUND_STATUS.REFUND_FAIL,
                modify_time=now2))
            return False, msg

        with transaction(db) as trans:
            # B账户退款
            db.execute(dbl.update_sp_balance(
                list_ret['spid'], 0 - list_ret['amount'],
                now2, const.ACCOUNT_CLASS.B))
            db.execute(t_sp_history.insert(), gen_sp_history_data(
                list_ret['spid'], 0 - list_ret['amount'],
                now2, const.ACCOUNT_CLASS.B))

            # 分乐B账户退款
            db.execute(dbl.update_fenle_balance(0 - list_ret['amount'], now2))
            db.execute(t_fenle_history.insert(), gen_fenle_history_data(
                0 - list_ret['amount'], now2))

            # 更新退款单状态\时间等
            db.execute(t_refund_list.update().where(
                t_refund_list.c.id == refund_id).values(
                status=const.REFUND_STATUS.REFUND_SUCCESS,
                modify_time=now2))

            db.execute(t_trans_list.update().where(
                t_trans_list.c.id == list_ret['id']).values(
                refund_id=refund_id, modify_time=now2))

            trans.finish()
        return True, gen_ret_data(
            const.REFUND_STATUS.REFUND_SUCCESS, now2)
    elif list_ret['settle_time'] is None:
        # 保存退款单，异步处理
        db.execute(t_refund_list.update().where(
            t_refund_list.c.id == refund_id).values(
            status=const.REFUND_STATUS.CHECKING,
            modify_time=now))
        return True, gen_ret_data(const.REFUND_STATUS.CHECKING, now)
    else:
        sp_amount = list_ret['amount'] - list_ret['fee']
        b_balance = dbl.get_sp_balance(
            db, list_ret['spid'], const.ACCOUNT_CLASS.B)
        if sp_amount <= b_balance:
            # 调用银行退款接口
            ok, msg = call_interface(is_settled=True)
            now2 = datetime.datetime.now()
            if not ok:
                db.execute(t_refund_list.update().where(
                    t_refund_list.c.id == refund_id).values(
                    status=const.REFUND_STATUS.REFUND_FAIL,
                    modify_time=now2))
                return False, msg

            with transaction(db) as trans:
                # B账户退款
                db.execute(dbl.update_sp_balance(
                    list_ret['spid'], 0 - sp_amount,
                    now2, const.ACCOUNT_CLASS.B))
                db.execute(t_sp_history.insert(), gen_sp_history_data(
                    list_ret['spid'], 0 - sp_amount,
                    now2, const.ACCOUNT_CLASS.B))

                # 分乐C账户退手续费
                db.execute(dbl.update_sp_balance(
                    config.FENLE_SPID, list_ret['bank_fee'] - list_ret['fee'],
                    now2, const.ACCOUNT_CLASS.C))
                db.execute(t_sp_history.insert(), gen_sp_history_data(
                    config.FENLE_SPID, list_ret['bank_fee'] - list_ret['fee'],
                    now2, const.ACCOUNT_CLASS.C))

                # 分乐B账户退款
                db.execute(dbl.update_fenle_balance(
                    list_ret['bank_fee'] - list_ret['amount'], now2))
                db.execute(t_fenle_history.insert(), gen_fenle_history_data(
                    list_ret['bank_fee'] - list_ret['amount'], now2))

                db.execute(t_refund_list.update().where(
                    t_refund_list.c.id == refund_id).values(
                    status=const.REFUND_STATUS.REFUND_SUCCESS,
                    modify_time=now2))

                db.execute(t_trans_list.update().where(
                    t_trans_list.c.id == list_ret['id']).values(
                    refund_id=refund_id, modify_time=now2))

                trans.finish()
            return True, gen_ret_data(const.REFUND_STATUS.REFUND_SUCCESS, now2)
        elif sp_amount - b_balance <= dbl.get_sp_balance(
                db, list_ret['spid'], const.ACCOUNT_CLASS.C):
            # 调用银行退款接口
            ok, msg = call_interface(is_settled=True)
            now2 = datetime.datetime.now()
            if not ok:
                db.execute(t_refund_list.update().where(
                    t_refund_list.c.id == refund_id).values(
                    status=const.REFUND_STATUS.REFUND_FAIL,
                    modify_time=now2))
                return False, msg

            with transaction(db) as trans:
                # C账户转账给B账户，以退款
                db.execute(dbl.update_sp_balance(
                    list_ret['spid'], b_balance - sp_amount,
                    now2, const.ACCOUNT_CLASS.C))
                db.execute(t_sp_history.insert(), gen_sp_history_data(
                    list_ret['spid'], b_balance - sp_amount,
                    now2, const.ACCOUNT_CLASS.C))
                # B账户接收C账户的汇款
                db.execute(dbl.update_sp_balance(
                    list_ret['spid'], sp_amount - b_balance,
                    now2, const.ACCOUNT_CLASS.B))
                db.execute(t_sp_history.insert(), gen_sp_history_data(
                    list_ret['spid'], sp_amount - b_balance,
                    now2, const.ACCOUNT_CLASS.B))

                # B账户退款
                db.execute(dbl.update_sp_balance(
                    list_ret['spid'], 0 - sp_amount,
                    now2, const.ACCOUNT_CLASS.B))
                db.execute(t_sp_history.insert(), gen_sp_history_data(
                    list_ret['spid'], 0 - sp_amount,
                    now2, const.ACCOUNT_CLASS.B))

                # 分乐C账户退手续费
                db.execute(dbl.update_sp_balance(
                    config.FENLE_SPID, list_ret['bank_fee'] - list_ret['fee'],
                    now2, const.ACCOUNT_CLASS.C))
                db.execute(t_sp_history.insert(), gen_sp_history_data(
                    config.FENLE_SPID, list_ret['bank_fee'] - list_ret['fee'],
                    now2, const.ACCOUNT_CLASS.C))

                # 分乐B账户退款
                db.execute(dbl.update_fenle_balance(
                    list_ret['bank_fee'] - list_ret['amount'], now2))
                db.execute(t_fenle_history.insert(), gen_fenle_history_data(
                    list_ret['bank_fee'] - list_ret['amount'], now2))

                db.execute(t_refund_list.update().where(
                    t_refund_list.c.id == refund_id).values(
                    status=const.REFUND_STATUS.REFUND_SUCCESS,
                    modify_time=now2))

                db.execute(t_trans_list.update().where(
                    t_trans_list.c.id == list_ret['id']).values(
                    refund_id=refund_id, modify_time=now2))
                trans.finish()
            return True, gen_ret_data(const.REFUND_STATUS.REFUND_SUCCESS, now2)
        else:
            return False, const.API_ERROR.REFUND_LESS_BALANCE

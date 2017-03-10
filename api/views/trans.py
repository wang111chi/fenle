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
    return ApiJsonOkResponse(trans=cipher_data)


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
    return ApiJsonOkResponse(trans=cipher_data)


def _cancel_or_refund(db, bank_list):
    is_ok, list_ret = dbl.get_list(
        db, bank_list, const.TRANS_STATUS.PAY_SUCCESS)
    if not is_ok:
        return False, list_ret

    now = datetime.datetime.now()
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

    sp_history_data = {
        'biz': const.BIZ.REFUND,
        'amount': list_ret['amount'],
        'ref_str_id': refund_id,  # 退款单号
        'create_time': now}
    fenle_history_data = sp_history_data.copy()

    sp_history_data.update({
        'spid': list_ret['spid'],
        'account_class': const.ACCOUNT_CLASS.B})

    fenle_history_data.update({
        'bankacc_no': config.FENLE_ACCOUNT_NO,
        'bank_type': config.FENLE_BANK_TYPE})

    ret_data = {'refund_id': refund_id,
                'amount': list_ret['amount']}  # 返回的数据
    for i in ('spid', 'list_id', 'status', 'modify_time'):
        ret_data[i] = refund_data[i]

    if now.date() == list_ret['modify_time'].date():
        # [TODO] 调用银行撤销接口
        # 更新status
        udp_sp_balance_b = dbl.update_sp_balance(
            list_ret['spid'], const.ACCOUNT_CLASS.B,
            0 - list_ret['amount'], now)

        udp_fenle_balance = t_fenle_balance.update().where(and_(
            t_fenle_balance.c.bankacc_no == config.FENLE_ACCOUNT_NO,
            t_fenle_balance.c.bank_type == config.FENLE_BANK_TYPE)).values(
            balance=t_fenle_balance.c.balance - list_ret['amount'],
            modify_time=now)

        udp_trans_list = t_trans_list.update().where(
            t_trans_list.c.id == list_ret['id']).values(
            refund_id=refund_id, modify_time=now)

        with transaction(db) as trans:
            db.execute(udp_sp_balance_b)
            db.execute(t_sp_history.insert(), sp_history_data)

            db.execute(udp_fenle_balance)
            db.execute(t_fenle_history.insert(), fenle_history_data)

            db.execute(t_refund_list.insert(), refund_data)
            db.execute(udp_trans_list)
            trans.finish()

        ret_data.update({"status": const.REFUND_STATUS.REFUND_SUCCESS})
        return True, ret_data
    elif list_ret['bank_settle_time'] is None:
        refund_data.update({'status': const.REFUND_STATUS.REFUNDING})
        db.execute(t_refund_list.insert(), refund_data)
        # 保存退款单，异步处理
        return True, ret_data
    else:
        sp_amount = list_ret['amount'] - list_ret['fee']
        sel_b = select([
            t_sp_balance.c.balance,
            t_sp_balance.c.freezing]).where(and_(
                t_sp_balance.c.spid == list_ret['spid'],
                t_sp_balance.c.cur_type == list_ret['cur_type'],
                t_sp_balance.c.account_class == const.ACCOUNT_CLASS.B))
        ret_sel_b = db.execute(sel_b).first()
        b_balance = ret_sel_b['balance'] - ret_sel_b['freezing']

        udp_trans_list = t_trans_list.update().where(
            t_trans_list.c.id == list_ret['id']).values(
            refund_id=refund_id, modify_time=now)

        if b_balance >= sp_amount:
            # [TODO] 调用银行撤销接口
            udp_sp_balance = dbl.update_sp_balance(
                list_ret['spid'], const.ACCOUNT_CLASS.B,
                0 - sp_amount, now)

            udp_spfen_balance = dbl.update_sp_balance(
                config.FENLE_SPID, const.ACCOUNT_CLASS.C,
                list_ret['bank_fee'] - list_ret['fee'], now)

            udp_fenle_balance = t_fenle_balance.update().where(and_(
                t_fenle_balance.c.bankacc_no == config.FENLE_ACCOUNT_NO,
                t_fenle_balance.c.bank_type == config.FENLE_BANK_TYPE)).values(
                balance=t_fenle_balance.c.balance +
                    list_ret['bank_fee'] - list_ret['amount'],
                modify_time=now)

            with transaction(db) as trans:
                db.execute(udp_fenle_balance)
                fenle_history_data.update({
                    'amount': list_ret['amount'] - list_ret['bank_fee']})
                db.execute(t_fenle_history.insert(), fenle_history_data)

                db.execute(udp_sp_balance)
                sp_history_data.update({'amount': sp_amount})
                db.execute(t_sp_history.insert(), sp_history_data)

                db.execute(udp_spfen_balance)
                sp_history_data.update({
                    'spid': config.FENLE_SPID,
                    'account_class': const.ACCOUNT_CLASS.C,
                    'amount': list_ret['fee'] - list_ret['bank_fee']})
                db.execute(t_sp_history.insert(), sp_history_data)

                db.execute(t_refund_list.insert(), refund_data)
                db.execute(udp_trans_list)
                trans.finish()
            ret_data.update({"status": const.REFUND_STATUS.REFUND_SUCCESS})
            return True, ret_data
        else:
            # [TODO] 调用银行退款接口
            sel_c = select([
                t_sp_balance.c.balance,
                t_sp_balance.c.freezing]).where(and_(
                    t_sp_balance.c.spid == list_ret['spid'],
                    t_sp_balance.c.cur_type == list_ret['cur_type'],
                    t_sp_balance.c.account_class == const.ACCOUNT_CLASS.C))
            ret_sel_c = db.execute(sel_c).first()
            c_balance = ret_sel_c['balance'] - ret_sel_c['freezing']
            if b_balance + c_balance >= sp_amount:
                udp_sp_balance_b2 = dbl.update_sp_balance(
                    list_ret['spid'], const.ACCOUNT_CLASS.B,
                    sp_amount - b_balance, now)
                udp_sp_balance_c = dbl.update_sp_balance(
                    list_ret['spid'], const.ACCOUNT_CLASS.C,
                    b_balance - sp_amount, now)

                udp_sp_balance_b = dbl.update_sp_balance(
                    list_ret['spid'], const.ACCOUNT_CLASS.B,
                    0 - sp_amount, now)

                udp_spfen_balance = dbl.update_sp_balance(
                    config.FENLE_SPID, const.ACCOUNT_CLASS.C,
                    list_ret['bank_fee'] - list_ret['fee'], now)

                udp_fenle_balance = t_fenle_balance.update().where(and_(
                    t_fenle_balance.c.bankacc_no == config.FENLE_ACCOUNT_NO,
                    t_fenle_balance.c.bank_type == config.FENLE_BANK_TYPE))\
                    .values(balance=t_fenle_balance.c.balance +
                            list_ret['bank_fee'] - list_ret['amount'],
                            modify_time=now)

                with transaction(db) as trans:
                    db.execute(udp_fenle_balance)
                    fenle_history_data.update({
                        'amount': list_ret['amount'] - list_ret['bank_fee']})
                    db.execute(t_fenle_history.insert(), fenle_history_data)

                    db.execute(udp_sp_balance_b2)
                    sp_history_data.update({
                        'amount': sp_amount - b_balance})
                    db.execute(t_sp_history.insert(), sp_history_data)

                    db.execute(udp_sp_balance_c)
                    sp_history_data.update({
                        'account_class': const.ACCOUNT_CLASS.C,
                        'amount': sp_amount - b_balance})
                    db.execute(t_sp_history.insert(), sp_history_data)

                    db.execute(udp_sp_balance_b)
                    sp_history_data.update({
                        'account_class': const.ACCOUNT_CLASS.B,
                        'amount': sp_amount})
                    db.execute(t_sp_history.insert(), sp_history_data)

                    db.execute(udp_spfen_balance)
                    sp_history_data.update({
                        'spid': config.FENLE_SPID,
                        'account_class': const.ACCOUNT_CLASS.C,
                        'amount': list_ret['fee'] - list_ret['bank_fee']})
                    db.execute(t_sp_history.insert(), sp_history_data)

                    db.execute(t_refund_list.insert(), refund_data)
                    db.execute(udp_trans_list)
                    trans.finish()
                ret_data.update({"status": const.REFUND_STATUS.REFUND_SUCCESS})
                return True, ret_data
            else:
                return False, const.API_ERROR.REFUND_LESS_BALANCE

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

from base.framework import get_list
from base.framework import get_sp_pubkey
from base.framework import db_conn
from base.framework import general
from base.framework import ApiJsonOkResponse
from base.framework import api_form_check
from base.framework import transaction
from base.framework import ApiJsonErrorResponse
from base.xform import F_mobile, F_str, F_int, F_datetime
from base import constant as const
from base import logger
from base import util
from base.db import engine, meta
from base.db import t_trans_list
from base.db import t_refund_list
from base.db import t_user_bank
from base.db import t_sp_bank
from base.db import t_bank_channel
from base.db import t_fenle_history
from base.db import t_sp_history
from base.db import t_fenle_balance
from base.db import t_sp_balance
from base.db import t_merchant_info
from base.xform import FormChecker
import config

home = Blueprint("home", __name__)


"""
@home.route("/")
@general("首页")
# @db_conn
def index():
    return "What do you want?"
"""


@home.route("/cardpay/validate")
@general("银行下发验证码")
@db_conn
@api_form_check({
    "spid": (10 <= F_str("商户号") <= 10) & "strict" & "required",
    "money": (F_int("订单交易金额")) & "strict" & "optional",
    "account_no": (F_str("付款人帐号") <= 16) & "strict" & "required",
    "user_mobile": (F_mobile("付款人手机号码")) & "strict" & "required",
    "bank_type": (F_str("银行代号") <= 4) & "strict" & "required",
    "sign": (F_str("签名") <= 1024) & "strict" & "required",
    "encode_type": (F_str("") <= 5) & "strict" & "required" & (
        lambda v: (v in const.ENCODE_TYPE.ALL, v)),
})
def cardpay_validate(db, safe_vars):
    """ 处理逻辑"""
    sel_sp_balance = select([t_sp_balance.c.spid]).where(
        t_sp_balance.c.spid == safe_vars['spid'])
    if db.execute(sel_sp_balance).first() is None:
        return ApiJsonErrorResponse(const.API_ERROR.SP_BALANCE_NOT_EXIST)

    # 检查银行渠道是否可用，是否验证手机号
    sel = select([t_bank_channel.c.is_enable]).where(
        t_bank_channel.c.bank_type == safe_vars['bank_type'])
    channel_ret = db.execute(sel).first()
    if channel_ret is None:
        return ApiJsonErrorResponse(const.API_ERROR.BANK_NOT_EXIST)
    if channel_ret['is_enable'] == const.BOOLEAN.FALSE:  # 银行渠道不可用
        return ApiJsonErrorResponse(const.API_ERROR.BANK_CHANNEL_UNABLE)

    # 检查用户银行卡信息 user_bank
    sel = select([t_user_bank.c.lstate]).where(
        t_user_bank.c.account_no == safe_vars['account_no'])
    user_bank_ret = db.execute(sel).first()
    now = datetime.datetime.now()
    if user_bank_ret is None:
        user_bank_info = {
            'account_no': safe_vars['account_no'],
            'account_type': const.ACCOUNT_TYPE.CREDIT_CARD,
            'bank_type': safe_vars['bank_type'],
            'account_mobile': safe_vars['user_mobile'],
            'status': const.USER_BANK_STATUS.INIT,
            'lstate': const.LSTATE.VALID,
            'create_time': now,
            'modify_time': now}
        db.execute(t_user_bank.insert(), user_bank_info)
    else:
        # 检查银行卡是否被冻结 user_bank
        if user_bank_ret['lstate'] == const.LSTATE.HUNG:  # 冻结标志
            return ApiJsonErrorResponse(const.API_ERROR.ACCOUNT_FREEZED)

    # 检查商户银行
    is_ok, ret_sp_bank = _check_sp_bank(
        db, safe_vars['spid'], safe_vars['bank_type'])
    if not is_ok:
        return ApiJsonErrorResponse(ret_sp_bank)

    # TODO 调用银行短信下发接口
    ret_data = {
        "bank_sms_time": now}  # 此处为银行返回时间
    sp_pubkey = get_sp_pubkey(db, safe_vars['spid'])
    cipher_data = util.rsa_sign_and_encrypt_params(
        ret_data, config.FENLE_PRIVATE_KEY, sp_pubkey)
    return ApiJsonOkResponse(cipher_data=cipher_data)


@home.route("/cardpay/trade")
@general("信用卡分期支付接口")
@db_conn
@api_form_check({
    "bank_sms_time": (F_str("短信下发时间") <= 32) & "strict" & "required",
    "spid": (10 <= F_str("商户号") <= 10) & "strict" & "required",
    "sp_userid": (F_str("用户号") <= 20) & "strict" & "optional",
    "sp_tid": (F_str("支付订单号") <= 32) & "strict" & "required",
    "money": (F_int("订单交易金额")) & "strict" & "required",
    "cur_type": (F_int("币种类型", const.CUR_TYPE.RMB)) & "strict" & "optional",
    "notify_url": (F_str("后台回调地址") <= 255) & "strict" & "required",
    "errpage_url": (F_str("错误页面回调地址") <= 255) & "strict" & "optional",
    "memo": (F_str("订单备注") <= 255) & "strict" & "required",
    "attach": (F_str("附加数据") <= 255) & "strict" & "optional",
    "account_type": F_int("银行卡类型", const.ACCOUNT_TYPE.CREDIT_CARD) & (
        "strict") & "required" & (lambda v: (v in const.ACCOUNT_TYPE.ALL, v)),
    "account_no": (F_str("付款人帐号") <= 16) & "strict" & "required",
    "user_name": (F_str("付款人姓名") <= 16) & "strict" & "optional",
    "user_mobile": (F_mobile("付款人手机号码")) & "strict" & "required",
    "bank_type": (F_str("银行代号") <= 4) & "strict" & "required",
    "expiration_date": (F_str("有效期") <= 11) & "strict" & "optional",
    "pin_code": (F_str("cvv2") <= 11) & "strict" & "optional",
    "divided_term": (F_int("分期期数")) & "strict" & "required",
    "fee_duty": (F_int("手续费承担方")) & "strict" & "required" & (
        lambda v: (v in const.FEE_DUTY.ALL, v)),
    "channel": (F_int("渠道类型", const.CHANNEL.API)) & "strict" & (
        "required") & (lambda v: (v in const.CHANNEL.ALL, v)),
    "sign": (F_str("签名") <= 1024) & "strict" & "required",
    "encode_type": (F_str("") <= 5) & "strict" & "required" & (
        lambda v: (v in const.ENCODE_TYPE.ALL, v)),
    "rist_ctrl": (F_str("风险控制数据") <= 10240) & "strict" & "optional",
})
def cardpay_trade(db, safe_vars):
    """ 处理逻辑"""
    sel_sp_balance = select([t_sp_balance.c.spid]).where(and_(
        t_sp_balance.c.spid == safe_vars['spid'],
        t_sp_balance.c.cur_type == safe_vars['cur_type']))
    if db.execute(sel_sp_balance).first() is None:
        return ApiJsonErrorResponse(const.API_ERROR.SP_BALANCE_NOT_EXIST)

    # 返回的参数
    ret_data = {'pay_type': const.PRODUCT_TYPE.FENQI}
    for k in ('spid', 'sp_tid', 'money', 'cur_type', 'divided_term',
              'fee_duty', 'encode_type'):
        ret_data[k] = safe_vars[k]

    sp_pubkey = get_sp_pubkey(db, safe_vars['spid'])
    # 检查商户订单号是否已经存在
    sel = select([t_trans_list.c.status, t_trans_list.c.list_id]).where(and_(
        t_trans_list.c.spid == safe_vars['spid'],
        t_trans_list.c.sp_tid == safe_vars['sp_tid']))
    list_ret = db.execute(sel).first()
    if list_ret is not None:   # 如果已经存在
        ret_data.update({
            "list_id": list_ret['list_id'],
            "result": list_ret['status'], })
        cipher_data = util.rsa_sign_and_encrypt_params(
            ret_data,
            config.FENLE_PRIVATE_KEY,
            sp_pubkey)
        return ApiJsonOkResponse(cipher_data=cipher_data)

    list_data = {
        'rsp_time': '3',
        'product_type': const.PRODUCT_TYPE.FENQI}

    # 检查银行渠道是否可用，
    is_ok, ret_channel = _check_bank_channel(db, safe_vars)
    if not is_ok:
        return ApiJsonErrorResponse(ret_channel)
    list_data['bank_channel'] = ret_channel['bank_channel']
    list_data['bank_fee'] = safe_vars[
        'money'] * ret_channel['bank_fee_percent'] // 10000

    # 检查用户银行卡信息 user_bank
    now = datetime.datetime.now()
    sel = select([t_user_bank.c.lstate]).where(
        t_user_bank.c.account_no == safe_vars['account_no'])
    user_bank_ret = db.execute(sel).first()
    if user_bank_ret is None:
        user_bank_info = {
            'account_no': safe_vars['account_no'],
            'account_type': safe_vars['account_type'],
            'bank_type': safe_vars['bank_type'],
            'account_mobile': safe_vars['user_mobile'],
            'status': const.USER_BANK_STATUS.INIT,
            'lstate': const.LSTATE.VALID,
            'create_time': now,
            'modify_time': now}
        db.execute(t_user_bank.insert(), user_bank_info)
    else:
        # 检查银行卡是否被冻结 user_bank
        if user_bank_ret['lstate'] == const.LSTATE.HUNG:  # 冻结标志
            return ApiJsonErrorResponse(const.API_ERROR.ACCOUNT_FREEZED)

    # 检查商户银行
    is_ok, ret_sp_bank = _check_sp_bank(
        db, safe_vars['spid'], safe_vars['bank_type'],
        safe_vars['divided_term'])
    if not is_ok:
        return ApiJsonErrorResponse(ret_sp_bank)
    bank_spid = ret_sp_bank['bank_spid']
    list_data['fee']\
        = safe_vars['money'] * ret_sp_bank['fee_percent'] // 10000

    # 生成订单相关数据
    list_data.update({
        'list_id': util.gen_trans_list_id(
            safe_vars['spid'], safe_vars['bank_type']),
        'bank_tid': util.gen_bank_tid(bank_spid),
        'bank_backid': "",
        'status': const.TRANS_STATUS.PAYING,  # 支付中
        'lstate': const.LSTATE.VALID,  # 有效的
        'create_time': now,
        'modify_time': now})

    # fee_duty  计算手续费生成金额
    if safe_vars['fee_duty'] == const.FEE_DUTY.BUSINESS:  # 商户付手续费
        list_data.update({
            'amount': safe_vars['money'],
            'paynum': safe_vars['money']})
    else:
        # 用户付手续费情形
        return ApiJsonErrorResponse(const.API_ERROR.NO_USER_PAY)

    # 更新订单字段
    for k in (u'spid', u'sp_tid', u'cur_type', u'notify_url',
              u'memo', u'account_no', u'account_type',
              u'user_mobile', u'bank_type', u'divided_term',
              u'fee_duty', u'channel'):
        list_data[k] = safe_vars[k]

    db.execute(t_trans_list.insert(), list_data)

    # TODO 调用银行支付请求接口,更新余额
    now = datetime.datetime.now()
    sp_history_data = {
        'biz': const.BIZ.TRANS,
        'amount': list_data['paynum'],
        'ref_str_id': list_data['list_id'],
        'create_time': now}
    fenle_history_data = sp_history_data.copy()

    sp_history_data.update({
        'spid': safe_vars['spid'],
        'account_class': const.ACCOUNT_CLASS.B})
    fenle_history_data.update({
        'account_no': list_data['account_no'],
        'account_type': list_data['account_type'],
        'bank_type': list_data['bank_type']})

    udp_sp_balance = _update_sp_balance(
        safe_vars['spid'], const.ACCOUNT_CLASS.B,
        list_data['paynum'], now)

    udp_fenle_balance = t_fenle_balance.update().where(and_(
        t_fenle_balance.c.account_no == config.FENLE_ACCOUNT_NO,
        t_fenle_balance.c.bank_type == config.FENLE_BANK_TYPE)).values(
        balance=t_fenle_balance.c.balance + list_data['paynum'],
        modify_time=now)

    udp_trans_list = t_trans_list.update().where(
        t_trans_list.c.list_id == list_data['list_id']).values(
        status=const.TRANS_STATUS.PAY_SUCCESS, modify_time=now,
        paysucc_time=now)

    with transaction(db) as trans:
        db.execute(t_sp_history.insert(), sp_history_data)
        db.execute(udp_sp_balance)
        db.execute(t_fenle_history.insert(), fenle_history_data)
        db.execute(udp_fenle_balance)
        db.execute(udp_trans_list)
        trans.finish()

    ret_data.update({
        "list_id": list_data['list_id'],
        "result": const.TRANS_STATUS.PAY_SUCCESS, })
    cipher_data = util.rsa_sign_and_encrypt_params(
        ret_data, config.FENLE_PRIVATE_KEY, sp_pubkey)
    return ApiJsonOkResponse(cipher_data=cipher_data)


@home.route("/cardpay/refund")
@general("退款接口")
@db_conn
@api_form_check({
    "sign": (F_str("签名") <= 1024) & "strict" & "required",
    "encode_type": (F_str("") <= 5) & "strict" & "required" & (
        lambda v: (v in const.ENCODE_TYPE.ALL, v)),
    "spid": (10 <= F_str("商户号") <= 10) & "strict" & "required",
    "list_id": (F_str("支付订单号") <= 32) & "strict" & "required",
})
def cardpay_refund(db, safe_vars):
    is_ok, list_ret = get_list(
        db, safe_vars['list_id'], const.TRANS_STATUS.PAY_SUCCESS)
    if not is_ok:
        return ApiJsonErrorResponse(list_ret)
    now = datetime.datetime.now()
    paysucc_time = list_ret['paysucc_time']
    # 退款单号
    refund_id = util.gen_refund_id(
        safe_vars['spid'], list_ret['bank_type'])

    refund_data = {
        'id': refund_id,
        'spid': safe_vars['spid'],
        'list_id': safe_vars['list_id'],
        'create_time': now,
        'modify_time': now,
        'status': const.BUINESS_STATUS.SUCCESS}

    sp_history_data = {
        'biz': const.BIZ.REFUND,
        'amount': list_ret['paynum'],
        'ref_str_id': refund_id,  # 退款单号
        'create_time': now}
    fenle_history_data = sp_history_data.copy()

    sp_history_data.update({
        'spid': safe_vars['spid'],
        'account_class': const.ACCOUNT_CLASS.B})
    fenle_history_data.update({
        'account_no': list_ret['account_no'],
        'account_type': list_ret['account_type'],
        'bank_type': list_ret['bank_type']})

    if now.date() == paysucc_time.date():
        # [TODO] 调用银行撤销接口
        # 更新status
        udp_sp_balance = _update_sp_balance(
            safe_vars['spid'], const.ACCOUNT_CLASS.B,
            0 - list_ret['paynum'], now)

        udp_fenle_balance = t_fenle_balance.update().where(and_(
            t_fenle_balance.c.account_no == config.FENLE_ACCOUNT_NO,
            t_fenle_balance.c.bank_type == config.FENLE_BANK_TYPE)).values(
            balance=t_fenle_balance.c.balance - list_ret['paynum'],
            modify_time=now)

        with transaction(db) as trans:
            db.execute(t_refund_list.insert(), refund_data)
            db.execute(t_sp_history.insert(), sp_history_data)
            db.execute(udp_sp_balance)
            db.execute(t_fenle_history.insert(), fenle_history_data)
            db.execute(udp_fenle_balance)
            trans.finish()
        return
    elif list_ret['settle_time'] is None:
        refund_data.update({'status': const.BUSINESS_STATUS.HANDLING})
        db.execute(t_refund_list.insert(), refund_data)
        # 保存退款单，异步处理
    else:
        sp_amount = list_ret['amount'] - list_ret['bank_fee']
        sel_b = select([
            t_sp_balance.c.balance,
            t_sp_balance.c.freezing]).where(and_(
                t_sp_balance.c.spid == safe_vars['spid'],
                t_sp_balance.c.cur_type == list_ret['cur_type'],
                t_sp_balance.c.account_class == const.ACCOUNT_CLASS.B))
        ret_sel_b = db.execute(sel_b).first()
        b_balance = ret_sel_b['balance'] - ret_sel_b['freezing']

        sp_history_data.update({'amount': sp_amount})
        fenle_history_data.update({'amount': sp_amount})
        if b_balance >= sp_amount:
            udp_sp_balance = _update_sp_balance(
                safe_vars['spid'], const.ACCOUNT_CLASS.B,
                0 - sp_amount, now)

            udp_spfen_balance = _update_sp_balance(
                config.FENLE_SPID, const.ACCOUNT_CLASS.C,
                list_ret['bankfee'] - list_ret['fee'], now)

            udp_fenle_balance = t_fenle_balance.update().where(and_(
                t_fenle_balance.c.account_no == config.FENLE_ACCOUNT_NO,
                t_fenle_balance.c.bank_type == config.FENLE_BANK_TYPE)).values(
                balance=t_fenle_balance.c.balance - sp_amount,
                modify_time=now)

            with transaction(db) as trans:
                db.execute(t_sp_history.insert(), sp_history_data)
                db.execute(udp_sp_balance)
                db.execute(t_fenle_history.insert(), fenle_history_data)
                db.execute(udp_fenle_balance)
                sp_history_data.update({
                    'account_class': const.ACCOUNT_CLASS.C,
                    'amount': list_ret['fee'] - list_ret['bank_fee']})
                db.execute(t_sp_history.insert(), sp_history_data)
                db.execute(udp_spfen_balance)
                db.execute(t_refund_list.insert(), refund_data)

                trans.finish()
        else:
            # [TODO] 调用银行退款接口
            sel_c = select([
                t_sp_balance.c.balance,
                t_sp_balance.c.freezing]).where(and_(
                    t_sp_balance.c.spid == safe_vars['spid'],
                    t_sp_balance.c.cur_type == list_ret['cur_type'],
                    t_sp_balance.c.account_class == const.ACCOUNT_CLASS.C))
            ret_sel_c = db.execute(sel_c).first()
            c_balance = ret_sel_c['balance'] - ret_sel_c['freezing']
            if b_balance + c_balance >= sp_amount:
                udp_sp_balance_b = _update_sp_balance(
                    safe_vars['spid'], const.ACCOUNT_CLASS.B, 0, now)

                udp_sp_balance_c = _update_sp_balance(
                    safe_vars['spid'], const.ACCOUNT_CLASS.C,
                    b_balance - sp_amount, now)

                udp_spfen_balance = _update_sp_balance(
                    config.FENLE_SPID, const.ACCOUNT_CLASS.C,
                    list_ret['bank_fee'] - list_ret['fee'], now)

                udp_fenle_balance = t_fenle_balance.update().where(and_(
                    t_fenle_balance.c.account_no == config.FENLE_ACCOUNT_NO,
                    t_fenle_balance.c.bank_type == config.FENLE_BANK_TYPE))\
                    .values(balance=t_fenle_balance.c.balance - sp_amount,
                            modify_time=now)
                with transaction(db) as trans:
                    db.execute(t_refund_list.insert(), refund_data)
                    db.execute(t_sp_history.insert(), sp_history_data)
                    db.execute(udp_sp_balance_b)
                    db.execute(t_fenle_history.insert(), fenle_history_data)
                    db.execute(udp_fenle_balance)
                    sp_history_data.update({
                        'account_class': const.ACCOUNT_CLASS.C})
                    db.execute(t_sp_history.insert(), sp_history_data)
                    db.execute(udp_sp_balance_c)
                    sp_history_data.update({
                        'amount': list_ret['fee'] - list_ret['bank_fee']})
                    db.execute(t_sp_history.insert(), sp_history_data)
                    db.execute(udp_spfen_balance)
                    trans.finish()
            else:
                return ApiJsonErrorResponse(
                    const.API_ERROR.REFUND_LESS_BALANCE)
    return


@home.route("/cardpay/query")
@general("单笔查询接口")
@db_conn
@api_form_check({
    "sign": (F_str("签名") <= 1024) & "strict" & "required",
    "encode_type": (F_str("") <= 5) & "strict" & "required" & (
        lambda v: (v in const.ENCODE_TYPE.ALL, v)),
    "spid": (10 <= F_str("商户号") <= 10) & "strict" & "required",
    "list_id": (F_str("支付订单号") <= 32) & "strict" & "required",
    "channel": (F_int("渠道类型", const.CHANNEL.API)) & "strict" & (
        "required") & (lambda v: (v in const.CHANNEL.ALL, v)),
    "rist_ctrl": (F_str("风险控制数据") <= 10240) & "strict" & "optional",
})
def cardpay_query(db, safe_vars):
    is_ok, list_ret = get_list(db, safe_vars['list_id'])
    if not is_ok:
        return ApiJsonErrorResponse(list_ret)
    sp_pubkey = get_sp_pubkey(db, safe_vars['spid'])
    ret_data = dict(list_ret).copy()
    ret_data.pop('paynum')
    ret_data.update({
        "money": list_ret['paynum'],
        "sign": safe_vars["sign"],
        "encode_type": safe_vars["encode_type"],
        "spid": safe_vars['spid'],
        "list_id": safe_vars['list_id'],
        "bank_name": const.BANK_ID.NAMES[list_ret["bank_type"]],
        "result": list_ret["status"]})
    cipher_data = util.rsa_sign_and_encrypt_params(
        ret_data, config.FENLE_PRIVATE_KEY, sp_pubkey)
    return ApiJsonOkResponse(cipher_data=cipher_data)


def _update_sp_balance(spid, account_class, balance, now,
                       cur_type=const.CUR_TYPE.RMB):
    """return a sql without execute"""
    return t_sp_balance.update().where(and_(
        t_sp_balance.c.spid == spid,
        t_sp_balance.c.cur_type == cur_type,
        t_sp_balance.c.account_class == account_class
    )).values(
        balance=t_sp_balance.c.balance + balance,
        modify_time=now)


def _check_bank_channel(db, safe_vars):
    sel = select([t_bank_channel.c.is_enable,
                  t_bank_channel.c.fenqi_fee_percent,
                  t_bank_channel.c.bank_valitype,
                  t_bank_channel.c.bank_channel,
                  t_bank_channel.c.singlepay_vmask]).where(
        t_bank_channel.c.bank_type == safe_vars['bank_type'])
    channel_ret = db.execute(sel).first()
    if channel_ret is None:
        return False, const.API_ERROR.BANK_NOT_EXIST

    if channel_ret['is_enable'] == const.BOOLEAN.FALSE:  # 银行渠道不可用
        return False, const.API_ERROR.BANK_CHANNEL_UNABLE

    if channel_ret['singlepay_vmask'] is not None:
        # 验证有效期
        if (channel_ret['singlepay_vmask'] & const.PAY_MASK.EXPIRATION) and \
           (safe_vars['expiration_date'] is None):
            return False, const.API_ERROR.NO_EXPIRATION_DATE

        # 验证安全码
        if (channel_ret['singlepay_vmask'] & const.PAY_MASK.PIN_CODE) and \
           (safe_vars['pin_code'] is None):
            return False, const.API_ERROR.NO_PIN_CODE

        # 验证姓名
        if (channel_ret['singlepay_vmask'] & const.PAY_MASK.NAME) and \
           (safe_vars['user_name'] is None):
            return False, const.API_ERROR.NO_USER_NAME

    fenqi_fee_percent = json.loads(channel_ret['fenqi_fee_percent'])
    if str(safe_vars['divided_term']) not in fenqi_fee_percent:
        return False, const.API_ERROR.DIVIDED_TERM_NOT_EXIST

    bank_fee_percent = fenqi_fee_percent[str(safe_vars['divided_term'])]
    result = {
        'bank_fee_percent': bank_fee_percent,
        'bank_channel': channel_ret['bank_channel']}
    if channel_ret['bank_valitype'] == const.BANK_VALITYPE.MOBILE_VALID:
        # 需要验证手机号
        result['is_need_mobile'] = True
    else:
        result['is_need_mobile'] = False
    return True, result


def _check_sp_bank(db, spid, bank_type, divided_term=6):
    """ 查 sp_bank 的 fenqi_fee_percent
        if not (set(safe_vars.keys()) >=
            set(('spid', 'bank_type', 'divided_term'))):
            return False, const.API_ERROR.PARAM_ERROR
    """
    sel = select([t_sp_bank.c.fenqi_fee_percent,
                  t_sp_bank.c.bank_spid]).where(and_(
                      t_sp_bank.c.spid == spid,
                      t_sp_bank.c.bank_type == bank_type))
    sp_bank_ret = db.execute(sel).first()
    if sp_bank_ret is None:
        return False, const.API_ERROR.NO_SP_BANK
    fenqi_fee_percent = json.loads(sp_bank_ret['fenqi_fee_percent'])
    if str(divided_term) not in fenqi_fee_percent:
        return False, const.API_ERROR.DIVIDED_TERM_NOT_EXIST
    result = {
        'fee_percent': divided_term,
        'bank_spid': sp_bank_ret['bank_spid']}
    return True, result


def _check_list(db, list_id, user_mobile, sp_tid, account_no):
    """检查订单状态"""
    sel = select([
        t_trans_list.c.status,
        t_trans_list.c.account_no,
        t_trans_list.c.user_mobile,
        t_trans_list.c.bank_type,
        t_trans_list.c.spid,
        t_trans_list.c.sp_tid,
        t_trans_list.c.cur_type,
        t_trans_list.c.fee_duty,
        t_trans_list.c.divided_term,
        t_trans_list.c.paynum,
        t_trans_list.c.fee,
        t_trans_list.c.bank_tid,
        t_trans_list.c.bank_backid,
        t_trans_list.c.bank_fee]).where(
        t_trans_list.c.list_id == list_id)
    list_ret = db.execute(sel).first()
    if list_ret is None:
        return False, const.API_ERROR.LIST_ID_NOT_EXIST

    if list_ret['status'] != const.TRANS_STATUS.MOBILE_CHECKING:
        return False, const.API_ERROR.CONFIRM_STATUS_ERROR

    if list_ret['user_mobile'] != user_mobile:
        return False, const.API_ERROR.CONFIRM_MOBILE_ERROR

    if list_ret['sp_tid'] != sp_tid:
        return False, const.API_ERROR.CONFIRM_SPTID_ERROR

    if list_ret['account_no'] != account_no:
        return False, const.API_ERROR.CONFIRM_ACCOUNT_NO_ERROR
    return True, list_ret

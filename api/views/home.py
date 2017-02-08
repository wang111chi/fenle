#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base64 import b64decode
import operator
import hashlib
import urllib
from datetime import datetime
import json
from itertools import chain

from flask import Blueprint, request
from sqlalchemy.sql import text, select, and_, or_
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Signature import PKCS1_v1_5 as sign_PKCS1_v1_5
from Crypto.Hash import SHA

from base.framework import db_conn
from base.framework import general
from base.framework import ApiJsonOkResponse
from base.framework import api_form_check
from base.framework import transaction
from base.framework import ApiJsonErrorResponse
from base.xform import F_mobile, F_str, F_int
from base import constant as const
from base import logger
from base import util
from base.db import engine, meta
from base.db import t_trans_list
from base.db import t_user_bank
from base.db import t_sp_bank
from base.db import t_bank_channel
from base.db import t_fenle_bankroll_list
from base.db import t_sp_bankroll_list
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


@home.route("/cardpay/apply")
@general("信用卡分期支付申请")
@db_conn
@api_form_check({
    "spid": (10 <= F_str("商户号") <= 10) & "strict" & "required",
    "sp_userid": (F_str("用户号") <= 20) & "strict" & "required",
    "sp_tid": (F_str("支付订单号") <= 32) & "strict" & "required",
    "money": (F_int("订单交易金额")) & "strict" & "required",
    "cur_type": (F_int("币种类型")) & "strict" & "required",
    "notify_url": (F_str("后台回调地址") <= 255) & "strict" & "required",
    "errpage_url": (F_str("错误页面回调地址") <= 255) & "strict" & "optional",
    "memo": (F_str("订单备注") <= 255) & "strict" & "required",
    "expire_time": (F_int("订单有效时长")) & "strict" & "optional",
    "attach": (F_str("附加数据") <= 255) & "strict" & "optional",
    "user_account_type": (F_int("银行卡类型")) & "strict" & "required" & (
        lambda v: (v in const.ACCOUNT_TYPE.ALL, v)),
    "user_account_attr": (F_int("用户类型")) & "strict" & "required" & (
        lambda v: (v in const.ACCOUNT_ATTR.ALL, v)),
    "user_account_no": (F_str("付款人帐号") <= 16) & "strict" & "required",
    "user_name": (F_str("付款人姓名") <= 16) & "strict" & "optional",
    "user_mobile": (F_mobile("付款人手机号码")) & "strict" & "required",
    "bank_type": (F_str("银行代号") <= 4) & "strict" & "required",
    "expiration_date": (F_str("有效期") <= 11) & "strict" & "optional",
    "pin_code": (F_str("cvv2") <= 11) & "strict" & "optional",
    "divided_term": (F_int("分期期数")) & "strict" & "required",
    "fee_duty": (F_int("手续费承担方")) & "strict" & "required" & (
        lambda v: (v in const.FEE_DUTY.ALL, v)),
    "channel": (F_int("渠道类型")) & "strict" & "required" & (
        lambda v: (v in const.CHANNEL.ALL, v)),
    "sign": (F_str("签名") <= 1024) & "strict" & "required",
    "encode_type": (F_str("") <= 5) & "strict" & "required" & (
        lambda v: (v in const.ENCODE_TYPE.ALL, v)),
    "rist_ctrl": (F_str("风险控制数据") <= 10240) & "strict" & "optional",
})
def cardpay_apply(db, safe_vars):
    # 处理逻辑

    is_ok, ret_merchant = _check_merchant(db,
                                          safe_vars['spid'],
                                          safe_vars['cur_type'])
    if not is_ok:
        return ApiJsonErrorResponse(ret_merchant)

    # 返回的参数
    ret_data = {'pay_type': const.PRODUCT_TYPE.FENQI}
    for k in ('spid', 'sp_tid', 'money', 'cur_type', 'divided_term',
              'fee_duty', 'user_account_type', 'encode_type'):
        ret_data[k] = safe_vars[k]

    # 检查商户订单号是否已经存在
    sel = select([t_trans_list.c.status, t_trans_list.c.list_id]).where(and_(
        t_trans_list.c.spid == safe_vars['spid'],
        t_trans_list.c.sp_tid == safe_vars['sp_tid']))
    list_ret = db.execute(sel).first()
    # merchant_pubkey = ret_merchant
    if list_ret is not None:   # 如果已经存在
        ret_data.update({
            "list_id": list_ret['list_id'],
            "result": list_ret['status'], })
        cipher_data = util.rsa_sign_and_encrypt_params(
            ret_data,
            config.FENLE_PRIVATE_KEY,
            ret_merchant)
        return ApiJsonOkResponse(cipher_data=cipher_data)

    comput_data = dict(
        rsp_time='3',
        product_type=const.PRODUCT_TYPE.FENQI,)

    # 检查银行渠道是否可用，是否验证手机号
    is_ok, ret_channel = _check_bank_channel(db, safe_vars)
    if not is_ok:
        return ApiJsonErrorResponse(ret_channel)
    comput_data['bank_channel'] = ret_channel['bank_channel']
    comput_data['bank_fee'] = safe_vars[
        'money'] * ret_channel['bank_fee_percent'] // 10000

    # 检查用户银行卡信息 user_bank
    now = datetime.now()
    sel = select([t_user_bank.c.lstate]).where(
        t_user_bank.c.account_no == safe_vars['user_account_no'])
    user_bank_ret = db.execute(sel).first()
    if user_bank_ret is None:
        user_bank_info = dict((k, safe_vars[k]) for k in (
            'user_account_no', 'user_name', 'bank_type', 'user_mobile'))
        user_bank_info.update({
            'status': const.USER_BANK_STATUS.INIT,
            'lstate': const.LSTATE.VALID,
            'account_type': safe_vars['user_account_type'],
            'account_attr': safe_vars['user_account_attr'],
            'create_time': now,
            'modify_time': now})
        db.execute(t_user_bank.insert(), user_bank_info)
    else:
        # 检查银行卡是否被冻结 user_bank
        if user_bank_ret['lstate'] == const.LSTATE.HUNG:  # 冻结标志
            return ApiJsonErrorResponse(const.API_ERROR.BANKCARD_FREEZED)

    # 检查商户银行
    is_ok, ret_sp_bank = _check_sp_bank(db, safe_vars)
    if not is_ok:
        return ApiJsonErrorResponse(ret_sp_bank)
    bank_spid = ret_sp_bank['bank_spid']
    comput_data['fee']\
        = safe_vars['money'] * ret_sp_bank['fee_percent'] // 10000

    # 生成订单相关数据
    comput_data.update({
        'list_id': util.gen_trans_list_id(
            safe_vars['spid'], safe_vars['bank_type']),
        'bank_tid': util.gen_bank_tid(bank_spid),
        'bank_backid': '',  # 暂时拟的
        'status': const.TRANS_STATUS.PAYING,  # 支付中
        'lstate': const.LSTATE.VALID,  # 有效的
        'create_time': now,
        'modify_time': now})

    # fee_duty  计算手续费生成金额
    if safe_vars['fee_duty'] == const.FEE_DUTY.BUSINESS:  # 商户付手续费
        comput_data.update({
            'amount': safe_vars['money'],
            'pay_num': safe_vars['money'], })
    else:
        # 用户付手续费情形
        return ApiJsonErrorResponse(const.API_ERROR.NO_USER_PAY)

    # 请求参数中的不需要计算的字段
    solid_field = (
        u'spid', u'sp_userid', u'sp_tid', u'cur_type',
        u'notify_url', u'memo', u'attach', u'user_account_no',
        u'user_account_type', u'user_account_attr',
        u'user_name', u'user_mobile', u'bank_type',
        u'divided_term', u'pin_code', u'fee_duty', u'channel')
    solid_data = dict((k, safe_vars[k]) for k in solid_field)

    if ret_channel['is_need_mobile']:
        comput_data.update({'status': const.TRANS_STATUS.MOBILE_CHECKING})
        db.execute(t_trans_list.insert(), dict(chain(
            comput_data.items(), solid_data.items())))

        # TODO 调用银行下发验证码，根据结果更新 bank_backid
        ret_data.update({
            "list_id": comput_data['list_id'],
            "result": comput_data['status'], })
        cipher_data = util.rsa_sign_and_encrypt_params(
            ret_data,
            config.FENLE_PRIVATE_KEY,
            ret_merchant)
        return ApiJsonOkResponse(cipher_data=cipher_data)
    else:
        db.execute(t_trans_list.insert(), dict(chain(
            comput_data.items(), solid_data.items())))

        # TODO 调用银行支付请求接口,更新余额
        now = datetime.now()
        sp_bankroll_data = dict((k, safe_vars[k]) for k in (
            'user_name', 'cur_type', 'bank_type', 'spid'))
        sp_bankroll_data['list_id'] = comput_data['list_id']
        sp_bankroll_data['product_type'] = const.PRODUCT_TYPE.FENQI
        sp_bankroll_data['create_time'] = now
        sp_bankroll_data['modify_time'] = now
        fenle_bankroll_data = sp_bankroll_data.copy()

        sp_bankroll_data.update({
            'bankroll_type': const.SP_BANKROLL_TYPE.TRANS,
            'list_sign': const.LIST_SIGN.WELL,
            'account_class': const.ACCOUNT_CLASS.B})

        fenle_bankroll_data.update({
            'fenle_account_id': config.FENLE_ACCOUNT_NO,
            'fenle_account_type': const.FENLE_ACCOUNT.VIRTUAL})  # 1真实，2虚拟

        # fee_duty  计算手续费生成金额
        if safe_vars['fee_duty'] == const.FEE_DUTY.BUSINESS:  # 商户付手续费
            sp_bankroll_data.update({
                'pay_num': comput_data['pay_num'],
                'sp_num': comput_data['pay_num'] - comput_data['fee']})
            fenle_bankroll_data.update({
                'pay_num': comput_data['pay_num'],
                'fact_amount': (comput_data['pay_num'] -
                                comput_data['bank_fee']),
                'income_num': comput_data['fee'] - comput_data['bank_fee']})
        else:
            # 用户付手续费情形
            return ApiJsonErrorResponse(const.API_ERROR.NO_USER_PAY)

        fenle_bankroll_data.update({
            'bank_tid': comput_data['bank_tid'],
            'bank_backid': comput_data['bank_backid']})

        udp_fenle_balance = t_fenle_balance.update().where(and_(
            t_fenle_balance.c.account_no == config.FENLE_ACCOUNT_NO,
            t_fenle_balance.c.bank_type == config.FENLE_BANK_TYPE)).values(
            balance=t_fenle_balance.c.balance +
                comput_data['fee'] - comput_data['bank_fee'],
            modify_time=now)
        udp_sp_balance = t_sp_balance.update().where(and_(
            t_sp_balance.c.spid == safe_vars['spid'],
            t_sp_balance.c.cur_type == safe_vars['cur_type'])).values(
            b_balance=t_sp_balance.c.b_balance +
                comput_data['pay_num'] - comput_data['fee'])
        udp_trans_list = t_trans_list.update().where(
            t_trans_list.c.list_id == comput_data['list_id']).values(
            status=const.TRANS_STATUS.PAY_SUCCESS)

        with transaction(db) as trans:
            db.execute(udp_trans_list)
            db.execute(t_sp_bankroll_list.insert(), sp_bankroll_data)
            db.execute(udp_sp_balance)
            db.execute(t_fenle_bankroll_list.insert(), fenle_bankroll_data)
            db.execute(udp_fenle_balance)
            trans.finish()

        ret_data.update({
            "list_id": comput_data['list_id'],
            "result": const.TRANS_STATUS.PAY_SUCCESS, })
        cipher_data = util.rsa_sign_and_encrypt_params(
            ret_data,
            config.FENLE_PRIVATE_KEY,
            ret_merchant)

        return ApiJsonOkResponse(cipher_data=cipher_data)


@home.route("/cardpay/confirm")
@general("信用卡分期支付确认")
@db_conn
@api_form_check({
    "spid": (10 <= F_str("商户号") <= 10) & "strict" & "required",
    "sign": (F_str("签名") <= 1024) & "strict" & "required",
    "encode_type": (F_str("") <= 5) & "strict" & "required" & (
        lambda v: (v in const.ENCODE_TYPE.ALL, v)),
    "list_id": (F_str("支付订单号") <= 32) & "strict" & "required",
    "user_mobile": (F_mobile("付款人手机号码")) & "strict" & "required",
    "bank_valicode": (F_str("银行下发的验证码") <= 32) & "strict" & "required",
})
def cardpay_confirm(db, safe_vars):
    is_ok, list_ret = _check_list(
        db, safe_vars['list_id'], safe_vars['user_mobile'])
    if not is_ok:
        return ApiJsonErrorResponse(list_ret)

    # TODO 用验证码调用银行接口
    now = datetime.now()
    sp_bankroll_data = dict((k, list_ret[k]) for k in (
        'spid', 'bank_type', 'cur_type'))
    sp_bankroll_data['create_time'] = now
    sp_bankroll_data['modify_time'] = now
    sp_bankroll_data['product_type'] = const.PRODUCT_TYPE.FENQI
    sp_bankroll_data['list_id'] = safe_vars['list_id']
    fenle_bankroll_data = sp_bankroll_data.copy()

    sp_bankroll_data.update({
        'bankroll_type': const.SP_BANKROLL_TYPE.TRANS,
        'list_sign': const.LIST_SIGN.WELL,
        'account_class': const.ACCOUNT_CLASS.B})

    fenle_bankroll_data.update({
        'product_type': const.PRODUCT_TYPE.FENQI,
        'fenle_account_id': config.FENLE_ACCOUNT_NO,
        'fenle_account_type': const.FENLE_ACCOUNT.VIRTUAL,  # 1真实，2虚拟
        'bank_tid': list_ret['bank_tid'],
        'bank_backid': list_ret['bank_backid']})

    # fee_duty  计算手续费生成金额
    if list_ret['fee_duty'] == const.FEE_DUTY.BUSINESS:  # 商户付手续费
        sp_bankroll_data.update({
            'pay_num': list_ret['paynum'],
            'sp_num': list_ret['paynum'] - list_ret['fee']})
        fenle_bankroll_data.update({
            'pay_num': list_ret['paynum'],
            'fact_amount': list_ret['paynum'] - list_ret['bank_fee'],
            'income_num': list_ret['fee'] - list_ret['bank_fee']})
    else:
        # 用户付手续费情形
        return ApiJsonErrorResponse(const.API_ERROR.NO_USER_PAY)

    fenle_bankroll_data.update({
        'bank_tid': list_ret['bank_tid'],
        'bank_backid': ""})

    udp_trans_list = t_trans_list.update().where(
        t_trans_list.c.list_id == safe_vars['list_id']).values(
        status=const.TRANS_STATUS.PAY_SUCCESS,
        bank_backid='321',
        modify_time=now)

    # 根据银行返回信息更新余额及流水
    udp_sp_balance = t_sp_balance.update().where(and_(
        t_sp_balance.c.spid == list_ret['spid'],
        t_sp_balance.c.cur_type == list_ret['cur_type'])).values(
        b_balance=t_sp_balance.c.b_balance +
            list_ret['paynum'] - list_ret['fee'],
        modify_time=now)
    udp_fenle_balance = t_fenle_balance.update().where(and_(
        t_fenle_balance.c.account_no == config.FENLE_ACCOUNT_NO,
        t_fenle_balance.c.bank_type == config.FENLE_BANK_TYPE)).values(
        balance=t_fenle_balance.c.balance +
            list_ret['fee'] - list_ret['bank_fee'],
        modify_time=now)
    with transaction(db) as trans:
        db.execute(udp_trans_list)
        db.execute(t_sp_bankroll_list.insert(), sp_bankroll_data)
        db.execute(udp_sp_balance)
        db.execute(t_fenle_bankroll_list.insert(), fenle_bankroll_data)
        db.execute(udp_fenle_balance)
        trans.finish()

    # 从mysql获取商户公钥
    s = select([t_merchant_info.c.rsa_pub_key]).where(
        t_merchant_info.c.spid == safe_vars['spid'])
    merchant_ret = db.execute(s).first()
    ret_merchant = merchant_ret['rsa_pub_key']
    ret_data = dict((k, list_ret[k]) for k in (
        'spid', 'sp_tid', 'paynum', 'cur_type', 'divided_term',
        'fee_duty', 'user_account_type'))
    ret_data.update({
        'pay_type': const.PRODUCT_TYPE.FENQI,
        'encode_type': safe_vars['encode_type'],
        "list_id": safe_vars['list_id'],
        "result": list_ret['status'], })
    cipher_data = util.rsa_sign_and_encrypt_params(
        ret_data,
        config.FENLE_PRIVATE_KEY,
        ret_merchant)

    return ApiJsonOkResponse(cipher_data=cipher_data)


@home.route("/query/single")
@general("单笔查询接口")
@db_conn
@api_form_check({
    "sign": (F_str("签名") <= 1024) & "strict" & "required",
    "encode_type": (F_str("") <= 5) & "strict" & "required" & (
        lambda v: (v in const.ENCODE_TYPE.ALL, v)),
    "spid": (10 <= F_str("商户号") <= 10) & "strict" & "required",
    "list_id": (F_str("支付订单号") <= 32) & "strict" & "required",
    "channel": (F_int("渠道类型")) & "strict" & "required" & (
        lambda v: (v in const.CHANNEL.ALL, v)),
    "rist_ctrl": (F_str("风险控制数据") <= 10240) & "strict" & "optional",
})
def single_query(db, safe_vars):
    sel = select([
        t_trans_list.c.status,
        t_trans_list.c.sp_userid,
        t_trans_list.c.sp_tid,
        t_trans_list.c.paynum,
        t_trans_list.c.fee,
        t_trans_list.c.cur_type,
        t_trans_list.c.divided_term,
        t_trans_list.c.fee_duty,
        t_trans_list.c.memo,
        t_trans_list.c.product_type,
        t_trans_list.c.bank_type]).where(
        t_trans_list.c.list_id == safe_vars['list_id'])

    list_ret = db.execute(sel).first()
    if list_ret is None:
        return ApiJsonErrorResponse(const.API_ERROR.LIST_ID_NOT_EXIST)
    sp_pubkey = _get_sp_pubkey(db, safe_vars['spid'])
    if not sp_pubkey[0]:
        return ApiJsonErrorResponse(sp_pubkey[1])
    ret_data = dict(list_ret).copy()
    ret_data.pop('paynum')
    ret_data.update({
        "sign": safe_vars["sign"],
        "encode_type": safe_vars["encode_type"],
        "spid": safe_vars['spid'],
        "bank_name": const.BANK_ID.NAMES[list_ret["bank_type"]],
        "result": list_ret["status"], })

    cipher_data = util.rsa_sign_and_encrypt_params(
        ret_data, config.FENLE_PRIVATE_KEY, sp_pubkey[1])

    return ApiJsonOkResponse(
        cipher_data=cipher_data,
        safe_vars=safe_vars)


def _check_merchant(db, spid, cur_type):
    """从mysql检查商户spid及状态信息"""

    sel_sp_balance = select([t_sp_balance.c.uid]).where(and_(
        t_sp_balance.c.spid == spid,
        t_sp_balance.c.cur_type == cur_type))
    if db.execute(sel_sp_balance).first() is None:
        return False, const.API_ERROR.SP_BALANCE_NOT_EXIST
    s = select([t_merchant_info.c.status,
                t_merchant_info.c.rsa_pub_key]).where(
        t_merchant_info.c.spid == spid)
    merchant_ret = db.execute(s).first()
    if merchant_ret is None:
        return False, const.API_ERROR.SPID_NOT_EXIST
    elif merchant_ret['status'] == const.MERCHANT_STATUS.FORBID:  # 判断是否被封禁
        return False, const.API_ERROR.MERCHANT_FORBID
    else:
        return True, merchant_ret['rsa_pub_key']


def _check_bank_channel(db, safe_vars):
    """
    检查银行渠道是否可用，是否验证手机号
    需要确保safe_vars包含以下字段:
    bank_type, expiration_date, pin_code, user_name, divided_term
    """
    if not set(('bank_type', 'divided_term', 'expiration_date',
                'pin_code', 'user_name')) <= set(safe_vars.keys()):
        return False, const.API_ERROR.PARAM_ERROR

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


def _check_sp_bank(db, safe_vars):
    """ 查 sp_bank 的 fenqi_fee_percent"""
    if not (set(safe_vars.keys()) >=
            set(('spid', 'bank_type', 'divided_term'))):
        return False, const.API_ERROR.PARAM_ERROR
    sel = select([t_sp_bank.c.fenqi_fee_percent,
                  t_sp_bank.c.bank_spid]).where(and_(
                      t_sp_bank.c.spid == safe_vars['spid'],
                      t_sp_bank.c.bank_type == safe_vars['bank_type']))
    sp_bank_ret = db.execute(sel).first()
    if sp_bank_ret is None:
        return False, const.API_ERROR.NO_SP_BANK
    fenqi_fee_percent = json.loads(sp_bank_ret['fenqi_fee_percent'])
    if str(safe_vars['divided_term']) not in fenqi_fee_percent:
        return False, const.API_ERROR.DIVIDED_TERM_NOT_EXIST
    result = {
        'fee_percent': fenqi_fee_percent[str(safe_vars['divided_term'])],
        'bank_spid': sp_bank_ret['bank_spid']}
    return True, result


def _check_list(db, list_id, user_mobile):
    """检查订单状态"""
    sel = select([
        t_trans_list.c.status,
        t_trans_list.c.user_account_no,
        t_trans_list.c.user_account_type,
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
    return True, list_ret


def _get_sp_pubkey(db, spid):
    """ 从mysql获取商户公钥"""
    s = select([t_merchant_info.c.rsa_pub_key]).where(
        t_merchant_info.c.spid == spid)
    merchant_ret = db.execute(s).first()
    if merchant_ret is None:
        return False, const.API_ERROR.SPID_NOT_EXIST
    else:
        return True, merchant_ret['rsa_pub_key']

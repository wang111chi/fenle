#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base64 import b64decode
import urlparse
import operator
import hashlib
import urllib
from datetime import datetime
import json

from flask import Blueprint, request
from sqlalchemy.sql import text, select, and_, or_
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Signature import PKCS1_v1_5 as sign_PKCS1_v1_5
from Crypto.Hash import SHA

from base.framework import db_conn
from base.framework import general
from base.framework import ApiJsonOkResponse
from base.framework import api_sign_and_encrypt_form_check
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
from base.db import t_merchant_info

# from base.db import *
from base.xform import FormChecker
import config

home = Blueprint("home", __name__)


@home.route("/")
@general("首页")
# @db_conn
def index():
    return "What do you want?"


@home.route("/cardpay/apply")
@general("信用卡分期支付申请")
@api_sign_and_encrypt_form_check(engine.connect(), {
    "spid": (10 <= F_str("商户号") <= 10) & "strict" & "required",
    "sign": (F_str("签名") <= 1024) & "strict" & "required",
    "encode_type": (F_str("") <= 5) & "strict" & "required" & (
        lambda v: (v in const.ENCODE_TYPE.ALL, v)),
    "sp_userid": (F_str("用户号") <= 20) & "strict" & "required",
    "sp_tid": (F_str("支付订单号") <= 32) & "strict" & "required",
    "money": (F_int("订单交易金额")) & "strict" & "required",
    "cur_type": (F_int("币种类型")) & "strict" & "required",
    "notify_url": (F_str("后台回调地址") <= 255) & "strict" & "required",
    "errpage_url": (F_str("错误页面回调地址") <= 255) & "strict" & "optional",
    "memo": (F_str("订单备注") <= 255) & "strict" & "required",
    "expire_time": (F_int("订单有效时长")) & "strict" & "optional",
    "attach": (F_str("附加数据") <= 255) & "strict" & "optional",
    "user_account_type": (F_int("银行卡类型")) & "strict" & "required",
    "user_account_attr": (F_int("用户类型")) & "strict" & "required",
    "user_account_no": (F_str("付款人帐号") <= 16) & "strict" & "required",
    "user_name": (F_str("付款人姓名") <= 16) & "strict" & "optional",
    "user_mobile": (F_mobile("付款人手机号码")) & "strict" & "required",
    "bank_type": (F_str("银行代号") <= 4) & "strict" & "required",
    "expiration_date": (F_str("有效期") <= 11) & "strict" & "optional",
    "pin_code": (F_str("cvv2") <= 11) & "strict" & "optional",
    "divided_term": (F_int("分期期数")) & "strict" & "required",
    "fee_duty": (F_int("手续费承担方")) & "strict" & "required",
    "channel": (F_int("渠道类型")) & "strict" & "required",
    "rist_ctrl": (F_str("风险控制数据") <= 10240) & "strict" & "optional",
})
def cardpay_apply(safe_vars):
    # 处理逻辑

    conn = engine.connect()
    # 从mysql检查商户spid是否存在
    s = select([t_merchant_info.c.status,
                t_merchant_info.c.mer_key,
                t_merchant_info.c.rsa_pub_key]).where(
        t_merchant_info.c.spid == safe_vars['spid'])
    merchant_ret = conn.execute(s).first()
    if merchant_ret is None:
        return ApiJsonErrorResponse(const.API_ERROR.SPID_NOT_EXIST)
    elif merchant_ret['status'] == const.MERCHANT_STATUS.CLOSURED:  # 判断是否被封禁
        return ApiJsonErrorResponse(const.API_ERROR.MERCHANT_CLOSURED)
    merchant_pubkey = merchant_ret['rsa_pub_key']

    # 预备返回的参数
    ret_data = dict(
        spid=safe_vars['spid'],
        sp_tid=safe_vars['sp_tid'],
        money=safe_vars['money'],
        cur_type=safe_vars['cur_type'],
        divided_term=safe_vars['divided_term'],
        fee_duty=safe_vars['fee_duty'],
        pay_type=const.PRODUCT_TYPE.FENQI,
        user_account_type=safe_vars['user_account_type'],
        encode_type=safe_vars['encode_type'], )

    # 检查商户订单号是否已经存在
    sel = select([t_trans_list.c.status, t_trans_list.c.list_id]).where(and_(
        t_trans_list.c.spid == safe_vars['spid'],
        t_trans_list.c.sp_tid == safe_vars['sp_tid']))
    list_ret = conn.execute(sel).first()
    if list_ret is not None:   # 如果已经存在
        ret_data.update({
            "list_id": list_ret['list_id'],
            "result": list_ret['status'], })
        cipher_data = util.rsa_sign_and_encrypt_params(
            ret_data,
            config.FENLE_PRIVATE_KEY,
            merchant_pubkey)
        return ApiJsonOkResponse(
            cipher_data=cipher_data,
            safe_vars=safe_vars,)

    # 请求参数中的不需要计算的字段
    solid_field = set((
        u'spid', u'sp_userid', u'sp_tid', u'cur_type',
        u'notify_url', u'memo', u'attach', u'user_account_no',
        u'user_account_type', u'user_account_attr',
        u'user_name', u'user_mobile', u'bank_type',
        u'divided_term', u'pin_code', u'fee_duty', u'channel'))
    solid_field = solid_field & set(safe_vars.keys())
    ''' other_field = (u'expiration_date', u'money', u'rist_ctrl',
    u'expire_time', u'errpage_url', u'encode_type', u'sign',)'''

    saved_data = dict()
    for k in solid_field:
        saved_data[k] = safe_vars[k]

    comput_data = dict(
        rsp_time='3',
        pay_type=const.PRODUCT_TYPE.FENQI,
        product_type=const.PRODUCT_TYPE.FENQI,)

    # 检查银行渠道是否可用，是否验证手机号
    sel = select([t_bank_channel.c.is_enable,
                  t_bank_channel.c.fenqi_fee_percent,
                  t_bank_channel.c.bank_valitype,
                  t_bank_channel.c.bank_channel,
                  t_bank_channel.c.singlepay_vmask]).where(
        t_bank_channel.c.bank_type == safe_vars['bank_type'])
    channel_ret = conn.execute(sel).first()
    if channel_ret is None:
        return ApiJsonErrorResponse(const.API_ERROR.BANK_NOT_EXIST)

    if channel_ret['is_enable'] == const.BOOLEAN.FALSE:  # 银行渠道不可用
        return ApiJsonErrorResponse(const.API_ERROR.BANK_CHANNEL_UNABLE)

    if channel_ret['singlepay_vmask'] is not None:
        # 验证有效期
        if (channel_ret['singlepay_vmask'] & const.PAY_MASK.EXPIRATION) and \
           ('expiration_date' not in safe_vars):
            return ApiJsonErrorResponse(const.API_ERROR.NO_EXPIRATION_DATE)

        # 验证安全码
        if (channel_ret['singlepay_vmask'] & const.PAY_MASK.PIN_CODE) and \
           ('pin_code' not in safe_vars):
            return ApiJsonErrorResponse(const.API_ERROR.NO_PIN_CODE)

        # 验证姓名
        if (channel_ret['singlepay_vmask'] & const.PAY_MASK.NAME) and \
           ('user_name' not in safe_vars):
            return ApiJsonErrorResponse(const.API_ERROR.NO_USER_NAME)

    if channel_ret['bank_valitype'] == const.BANK_VALITYPE.MOBILE_VALID:
        # 需要验证手机号
        is_need_mobile = True
    else:
        is_need_mobile = False
    bank_fee_percent = json.loads(channel_ret['fenqi_fee_percent'])
    if str(safe_vars['divided_term']) not in bank_fee_percent:
        return ApiJsonErrorResponse(const.API_ERROR.DIVIDED_TERM_NOt_EXIST)
    comput_data.update({
        'bank_channel': channel_ret['bank_channel'],
        'bank_fee': bank_fee_percent[str(safe_vars['divided_term'])] *
        safe_vars['money'] / 10000})

    # 检查用户银行卡信息 user_bank
    now = datetime.now()
    sel = select([t_user_bank.c.lstate]).where(
        t_user_bank.c.account_no == safe_vars['user_account_no'])
    user_bank_ret = conn.execute(sel).first()
    if user_bank_ret is None:
        user_bank_info = dict(
            account_no=safe_vars['user_account_no'],
            account_type=safe_vars['user_account_type'],
            account_attr=safe_vars['user_account_type'],
            user_name=safe_vars['user_name'],
            bank_type=safe_vars['bank_type'],
            bank_sname='',
            bank_branch='',
            mobile=safe_vars['user_mobile'],
            state=1,
            lstate=1,
            create_time=now,
            modify_time=now)
        conn.execute(t_user_bank.insert(), user_bank_info)
    else:
        # 检查银行卡是否被冻结 user_bank
        if user_bank_ret['lstate'] == 2:  # 冻结标志
            return ApiJsonErrorResponse(const.API_ERROR.BANKCARD_FREEZED)

    # 检查合同信息

    # 查 sp_bank 的 fenqi_fee_percent
    sel = select([t_sp_bank.c.fenqi_fee_percent,
                  t_sp_bank.c.divided_term]).where(and_(
                      t_sp_bank.c.spid == safe_vars['spid'],
                      t_sp_bank.c.bank_type == safe_vars['bank_type']))
    sp_bank_ret = conn.execute(sel).first()
    if sp_bank_ret is None:
        return ApiJsonErrorResponse(const.API_ERROR.NO_SP_BANK)

    if not str(safe_vars['divided_term']) in \
            sp_bank_ret['divided_term'].split(','):
        return ApiJsonErrorResponse(const.API_ERROR.DIVIDED_TERM_NOt_EXIST)

    fenqi_fee_percent = json.loads(sp_bank_ret['fenqi_fee_percent'])
    if str(safe_vars['divided_term']) not in fenqi_fee_percent:
        return ApiJsonErrorResponse(const.API_ERROR.DIVIDED_TERM_NOt_EXIST)
    fee_percent = fenqi_fee_percent[str(safe_vars['divided_term'])]
    comput_data.update({'fee': safe_vars['money'] * fee_percent / 10000})

    # 生成订单相关数据
    comput_data.update(dict(
        list_id=33,   # 暂时拟定33
        bank_tid='123',  # 暂时拟的
        bank_backid='321',  # 暂时拟的
        status=const.STATUS.PAYING,  # 支付中
        lstate=const.LSTATE.VALID,  # 有效的
        create_time=now,
        modify_time=now))
    ins_trans_list = t_trans_list.insert().values(**saved_data)

    # fee_duty  计算手续费生成金额
    if safe_vars['fee_duty'] == const.FEE_DUTY.BUSINESS:  # 商户付手续费
        comput_data.update({
            'amount': safe_vars['money'],
            'pay_num': safe_vars['money'], })
    else:
        pass
        # TODO 用户付手续费情形

    if is_need_mobile:
        conn.execute(ins_trans_list, comput_data)
        # TODO 调用银行接口，根据结果更新 bank_backid
        ret_data.update({
            "list_id": comput_data['list_id'],
            "result": const.STATUS.MOBILE_CHECKING, })
        cipher_data = util.rsa_sign_and_encrypt_params(
            ret_data,
            config.FENLE_PRIVATE_KEY,
            merchant_pubkey)
        return ApiJsonOkResponse(
            cipher_data=cipher_data,
            safe_vars=safe_vars)
    else:
        sp_bankroll_data = dict(
            list_id=comput_data['list_id'],
            spid=safe_vars['spid'],
            bankroll_type=const.BANKROLL_TYPE.IN,
            status=const.STATUS.MOBILE_CHECKING,  # 支付中
            user_name=safe_vars['user_name'],
            cur_type=safe_vars['cur_type'],
            bank_type=safe_vars['bank_type'],
            create_time=comput_data['create_time'],
            modify_time=comput_data['modify_time'],
            product_type=const.PRODUCT_TYPE.FENQI,
            list_sign=const.LIST_SIGN.WELL)

        fenle_bankroll_data = dict(
            list_id=comput_data['list_id'],
            spid=safe_vars['spid'],
            fenle_account_id=1234567890123123,
            fenle_account_type=const.FENLE_ACCOUNT.VIRTUAL,  # 1真实，2虚拟
            status=const.STATUS.MOBILE_CHECKING,  # 支付中
            bank_type=safe_vars['bank_type'],
            cur_type=safe_vars['cur_type'],
            user_name=safe_vars['user_name'],
            create_time=comput_data['create_time'],
            modify_time=comput_data['modify_time'],
            product_type=const.PRODUCT_TYPE.FENQI, )

        # fee_duty  计算手续费生成金额
        if safe_vars['fee_duty'] == const.FEE_DUTY.BUSINESS:  # 商户付手续费
            sp_bankroll_data.update({
                'pay_num': comput_data['pay_num'], 'sp_num':
                comput_data['pay_num'] - comput_data['fee']})
            fenle_bankroll_data.update({
                'pay_num': comput_data['pay_num'],
                'fact_amount':
                comput_data['pay_num'] - comput_data['bank_fee'],
                'income_num': comput_data['fee'] - comput_data['bank_fee']})
        else:
            pass
            # TODO 用户付手续费情形

        with transaction(conn) as trans:
            conn.execute(ins_trans_list, comput_data)
            fenle_bankroll_data.update({
                'bank_tid': '987654321', 'bank_backid': '0987654321'})
            conn.execute(t_sp_bankroll_list.insert(), sp_bankroll_data)
            conn.execute(t_fenle_bankroll_list.insert(), fenle_bankroll_data)
            # TODO 调用银行支付请求接口
            # if xxxxx:
            #     if you don't want to commit,
            #        you just not call trans.finish().
            #     return error_page("xxxxxx")
            # if you want to commit, you call:
            trans.finish()

        ret_data.update({
            "list_id": comput_data['list_id'],
            "result": const.STATUS.PAY_SUCCESS, })
        cipher_data = util.rsa_sign_and_encrypt_params(
            ret_data,
            config.FENLE_PRIVATE_KEY,
            merchant_pubkey)
        return ApiJsonOkResponse(
            cipher_data=cipher_data,
            safe_vars=safe_vars, )

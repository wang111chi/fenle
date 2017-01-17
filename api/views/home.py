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
from base.db import t_fenle_balance
from base.db import t_sp_balance
from base.db import t_merchant_info
from base.xform import FormChecker
import config

home = Blueprint("home", __name__)


@home.route("/")
@general("首页")
# @db_conn
def index():
    return "What do you want?"


# 提取函数返回结构{'is_ok':False, 'result':const.*.*}
# 从mysql检查商户spid及状态信息
def check_merchant(db, spid, cur_type):
    sel_sp_balance = select([t_sp_balance.c.id]).where(and_(
        t_sp_balance.c.spid == spid,
        t_sp_balance.c.cur_type == cur_type))
    ret = {'is_ok': False}
    if db.execute(sel_sp_balance).first() is None:
        ret['result'] = const.API_ERROR.SP_BALANCE_NOT_EXIST
        return ret
    s = select([t_merchant_info.c.status,
                t_merchant_info.c.rsa_pub_key]).where(
        t_merchant_info.c.spid == spid)
    merchant_ret = db.execute(s).first()
    if merchant_ret is None:
        ret['result'] = const.API_ERROR.SPID_NOT_EXIST
    elif merchant_ret['status'] == const.MERCHANT_STATUS.FORBID:  # 判断是否被封禁
        ret['result'] = const.API_ERROR.MERCHANT_FORBID
    else:
        ret['is_ok'] = True
        ret['result'] = {'merchant_pubkey': merchant_ret['rsa_pub_key']}
    return ret


# 检查银行渠道是否可用，是否验证手机号
def check_bank_channel(db, safe_vars):
    """
    需要确保safe_vars包含以下字段:
    bank_type, expiration_date, pin_code, user_name, divided_term
    """
    ret = {'is_ok': False}
    if not set(('bank_type', 'divided_term', 'expiration_date',
                'pin_code', 'user_name')) <= set(safe_vars.keys()):
        ret['result'] = const.API_ERROR.PARAM_ERROR
        return ret

    sel = select([t_bank_channel.c.is_enable,
                  t_bank_channel.c.fenqi_fee_percent,
                  t_bank_channel.c.bank_valitype,
                  t_bank_channel.c.bank_channel,
                  t_bank_channel.c.singlepay_vmask]).where(
        t_bank_channel.c.bank_type == safe_vars['bank_type'])
    channel_ret = db.execute(sel).first()
    if channel_ret is None:
        ret['result'] = const.API_ERROR.BANK_NOT_EXIST
        return ret

    if channel_ret['is_enable'] == const.BOOLEAN.FALSE:  # 银行渠道不可用
        ret['result'] = const.API_ERROR.BANK_CHANNEL_UNABLE
        return ret

    if channel_ret['singlepay_vmask'] is not None:
        # 验证有效期
        if (channel_ret['singlepay_vmask'] & const.PAY_MASK.EXPIRATION) and \
           (safe_vars['expiration_date'] is None):
            ret['result'] = const.API_ERROR.NO_EXPIRATION_DATE
            return ret

        # 验证安全码
        if (channel_ret['singlepay_vmask'] & const.PAY_MASK.PIN_CODE) and \
           (safe_vars['pin_code'] is None):
            ret['result'] = const.API_ERROR.NO_PIN_CODE
            return ret

        # 验证姓名
        if (channel_ret['singlepay_vmask'] & const.PAY_MASK.NAME) and \
           (safe_vars['user_name'] is None):
            ret['result'] = const.API_ERROR.NO_USER_NAME
            return ret

    fenqi_fee_percent = json.loads(channel_ret['fenqi_fee_percent'])
    if str(safe_vars['divided_term']) not in fenqi_fee_percent:
        ret['result'] = const.API_ERROR.DIVIDED_TERM_NOT_EXIST
        return ret

    ret['is_ok'] = True
    bank_fee_percent = fenqi_fee_percent[str(safe_vars['divided_term'])]
    ret['result'] = {
        'bank_fee_percent': bank_fee_percent,
        'bank_channel': channel_ret['bank_channel']}
    if channel_ret['bank_valitype'] == const.BANK_VALITYPE.MOBILE_VALID:
        # 需要验证手机号
        ret['result']['is_need_mobile'] = True
    else:
        ret['result']['is_need_mobile'] = False
    return ret


# 查 sp_bank 的 fenqi_fee_percent
def check_sp_bank(db, safe_vars):
    ret = {'is_ok': False}
    if not (set(safe_vars.keys()) >=
            set(('spid', 'bank_type', 'divided_term'))):
        ret['result'] = const.API_ERROR.PARAM_ERROR
        return ret
    sel = select([t_sp_bank.c.fenqi_fee_percent,
                  t_sp_bank.c.bank_spid]).where(and_(
                      t_sp_bank.c.spid == safe_vars['spid'],
                      t_sp_bank.c.bank_type == safe_vars['bank_type']))
    sp_bank_ret = db.execute(sel).first()
    if sp_bank_ret is None:
        ret['result'] = const.API_ERROR.NO_SP_BANK
        return ret
    fenqi_fee_percent = json.loads(sp_bank_ret['fenqi_fee_percent'])
    if str(safe_vars['divided_term']) not in fenqi_fee_percent:
        ret['result'] = const.API_ERROR.DIVIDED_TERM_NOT_EXIST
        return ret
    fee_percent = fenqi_fee_percent[str(safe_vars['divided_term'])]
    ret['is_ok'] = True
    ret['result'] = {'fee_percent': fee_percent,
                     'bank_spid': sp_bank_ret['bank_spid']}
    return ret


@home.route("/cardpay/apply")
@general("信用卡分期支付申请")
@db_conn
@api_sign_and_encrypt_form_check({
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
    "rist_ctrl": (F_str("风险控制数据") <= 10240) & "strict" & "optional",
})
def cardpay_apply(db, safe_vars):
    # 处理逻辑

    ret_merchant = check_merchant(db, safe_vars['spid'], safe_vars['cur_type'])
    if not ret_merchant['is_ok']:
        return ApiJsonErrorResponse(ret_merchant['result'])

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
    merchant_pubkey = ret_merchant['result']['merchant_pubkey']
    if list_ret is not None:   # 如果已经存在
        ret_data.update({
            "list_id": list_ret['list_id'],
            "result": list_ret['status'], })
        ret_data = util.encode_unicode(ret_data)
        cipher_data = util.rsa_sign_and_encrypt_params(
            ret_data,
            config.FENLE_PRIVATE_KEY,
            merchant_pubkey)
        return ApiJsonOkResponse(
            cipher_data=cipher_data,
            safe_vars=safe_vars,)

    comput_data = dict(
        rsp_time='3',
        product_type=const.PRODUCT_TYPE.FENQI,)

    # 检查银行渠道是否可用，是否验证手机号
    ret_channel = check_bank_channel(db, safe_vars)
    if not ret_channel['is_ok']:
        return ApiJsonErrorResponse(ret_channel['result'])
    comput_data['bank_channel'] = ret_channel['result']['bank_channel']
    comput_data['bank_fee'] = safe_vars[
        'money'] * ret_channel['result']['bank_fee_percent'] / 10000

    # 检查用户银行卡信息 user_bank
    now = datetime.now()
    sel = select([t_user_bank.c.lstate]).where(
        t_user_bank.c.account_no == safe_vars['user_account_no'])
    user_bank_ret = db.execute(sel).first()
    if user_bank_ret is None:
        user_bank_info = dict(
            account_no=safe_vars['user_account_no'],
            account_type=safe_vars['user_account_type'],
            account_attr=safe_vars['user_account_attr'],
            user_name=safe_vars['user_name'],
            bank_type=safe_vars['bank_type'],
            bank_sname='',
            bank_branch='',
            mobile=safe_vars['user_mobile'],
            state=const.USER_BANK_STATUS.INIT,
            lstate=const.LSTATE.VALID,
            create_time=now,
            modify_time=now)
        db.execute(t_user_bank.insert(), user_bank_info)
    else:
        # 检查银行卡是否被冻结 user_bank
        if user_bank_ret['lstate'] == const.LSTATE.HUNG:  # 冻结标志
            return ApiJsonErrorResponse(const.API_ERROR.BANKCARD_FREEZED)

    # 检查商户银行
    ret_sp_bank = check_sp_bank(db, safe_vars)
    if not ret_sp_bank['is_ok']:
        return ApiJsonErrorResponse(ret_sp_bank['result'])
    bank_spid = ret_sp_bank['result']['bank_spid']
    comput_data['fee']\
        = safe_vars['money'] * ret_sp_bank['result']['fee_percent'] / 10000

    # 生成订单相关数据
    comput_data.update(dict(
        list_id=util.gen_trans_list_id(
            safe_vars['spid'],
            safe_vars['bank_type']),
        bank_tid=util.gen_bank_tid(bank_spid),
        bank_backid='',  # 暂时拟的
        status=const.TRANS_STATUS.PAYING,  # 支付中
        lstate=const.LSTATE.VALID,  # 有效的
        create_time=now,
        modify_time=now))

    # fee_duty  计算手续费生成金额
    if safe_vars['fee_duty'] == const.FEE_DUTY.BUSINESS:  # 商户付手续费
        comput_data.update({
            'amount': safe_vars['money'],
            'pay_num': safe_vars['money'], })
    else:
        # 用户付手续费情形
        return ApiJsonErrorResponse(const.API_ERROR.NO_USER_PAY)

    # 请求参数中的不需要计算的字段
    solid_field = set((
        u'spid', u'sp_userid', u'sp_tid', u'cur_type',
        u'notify_url', u'memo', u'attach', u'user_account_no',
        u'user_account_type', u'user_account_attr',
        u'user_name', u'user_mobile', u'bank_type',
        u'divided_term', u'pin_code', u'fee_duty', u'channel'))
    ''' other_field = (u'expiration_date', u'money', u'rist_ctrl',
    u'expire_time', u'errpage_url', u'encode_type', u'sign',)'''
    solid_data = dict((k, safe_vars[k]) for k in solid_field)

    if ret_channel['result']['is_need_mobile']:
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
            merchant_pubkey)
        return ApiJsonOkResponse(
            list_id=comput_data['list_id'],
            cipher_data=cipher_data,
            safe_vars=safe_vars)
    else:
        sp_bankroll_data = dict(
            list_id=comput_data['list_id'],
            spid=safe_vars['spid'],
            bankroll_type=const.SP_BANKROLL_TYPE.IN,
            status=const.TRANS_STATUS.MOBILE_CHECKING,  # 支付中
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
            fenle_account_id=config.FENLE_ACCOUNT_NO,
            fenle_account_type=const.FENLE_ACCOUNT.VIRTUAL,  # 1真实，2虚拟
            status=const.TRANS_STATUS.MOBILE_CHECKING,  # 支付中
            bank_type=safe_vars['bank_type'],
            cur_type=safe_vars['cur_type'],
            user_name=safe_vars['user_name'],
            create_time=comput_data['create_time'],
            modify_time=comput_data['modify_time'],
            product_type=const.PRODUCT_TYPE.FENQI, )

        # fee_duty  计算手续费生成金额
        if safe_vars['fee_duty'] == const.FEE_DUTY.BUSINESS:  # 商户付手续费
            sp_bankroll_data.update({
                'pay_num': comput_data['pay_num'],
                'sp_num': (comput_data['pay_num'] -
                           comput_data['fee'])
            })
            fenle_bankroll_data.update({
                'pay_num': comput_data['pay_num'],
                'fact_amount': (comput_data['pay_num'] -
                                comput_data['bank_fee']),
                'income_num': comput_data['fee'] - comput_data['bank_fee']
            })
        else:
            # 用户付手续费情形
            return ApiJsonErrorResponse(const.API_ERROR.NO_USER_PAY)
        fenle_bankroll_data.update({
            'bank_tid': comput_data['bank_tid'],
            'bank_backid': comput_data['bank_backid']})

        with transaction(db) as trans:
            db.execute(t_trans_list.insert(), comput_data)
            ret = db.execute(t_sp_bankroll_list.insert(), sp_bankroll_data)
            last_id = ret._saved_cursor._last_insert_id
            db.execute(t_fenle_bankroll_list.insert(), fenle_bankroll_data)
            trans.finish()

        # TODO 调用银行支付请求接口,更新余额
        now = datetime.now()
        udp_fenle_bankroll = t_fenle_bankroll_list.update().where(and_(
            t_fenle_bankroll_list.c.bank_tid == comput_data['bank_tid'],
            t_fenle_bankroll_list.c.bank_type == safe_vars['bank_type']))\
            .values(status=const.TRANS_STATUS.PAY_SUCCESS, modify_time=now)

        udp_fenle_balance = t_fenle_balance.update().where(and_(
            t_fenle_balance.c.account_no == config.FENLE_ACCOUNT_NO,
            t_fenle_balance.c.bank_type == config.FENLE_BANK_TYPE)).values(
            balance=t_fenle_balance.c.balance +
                comput_data['fee'] - comput_data['bank_fee'],
            modify_time=now)

        udp_sp_bankroll = t_sp_bankroll_list.update().where(
            t_sp_bankroll_list.c.id == last_id).values(
            status=const.TRANS_STATUS.PAY_SUCCESS,
            modify_time=now)

        # FIXME: review by liyuan: 商家余额可能还不存在(第一次)，这时需要插入新的，
        # 可以用insert on duplidate update语法
        udp_sp_balance = t_sp_balance.update().where(and_(
            t_sp_balance.c.spid == safe_vars['spid'],
            t_sp_balance.c.cur_type == safe_vars['cur_type'])).values(
            balance=t_sp_balance.c.balance +
                comput_data['pay_num'] - comput_data['fee'])

        udp_trans_list = t_trans_list.update().where(
            t_trans_list.c.list_id == comput_data['list_id']).values(
            status=const.TRANS_STATUS.PAY_SUCCESS)

        with transaction(db) as trans:
            db.execute(udp_fenle_bankroll)
            db.execute(udp_fenle_balance)
            db.execute(udp_sp_bankroll)
            db.execute(udp_sp_balance)
            db.execute(udp_trans_list)
            trans.finish()

        ret_data.update({
            "list_id": comput_data['list_id'],
            "result": const.TRANS_STATUS.PAY_SUCCESS, })
        ret_data = util.encode_unicode(ret_data)
        cipher_data = util.rsa_sign_and_encrypt_params(
            ret_data,
            config.FENLE_PRIVATE_KEY,
            merchant_pubkey)
        return ApiJsonOkResponse(
            list_id=comput_data['list_id'],
            cipher_data=cipher_data,
            safe_vars=safe_vars, )


@home.route("/cardpay/confirm")
@general("信用卡分期支付确认")
@db_conn
@api_sign_and_encrypt_form_check({
    "spid": (10 <= F_str("商户号") <= 10) & "strict" & "required",
    "sign": (F_str("签名") <= 1024) & "strict" & "required",
    "encode_type": (F_str("") <= 5) & "strict" & "required" & (
        lambda v: (v in const.ENCODE_TYPE.ALL, v)),
    "list_id": (F_str("支付订单号") <= 32) & "strict" & "required",
    "user_mobile": (F_mobile("付款人手机号码")) & "strict" & "required",
    "bank_valicode": (F_str("银行下发的验证码") <= 32) & "strict" & "required",
})
def cardpay_confirm(db, safe_vars):

    # 检查订单状态
    sel = select([t_trans_list.c.status,
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
        t_trans_list.c.list_id == safe_vars['list_id'])
    list_ret = db.execute(sel).first()
    if list_ret is None:
        return ApiJsonErrorResponse(const.API_ERROR.LIST_ID_NOT_EXIST)

    if list_ret['status'] != const.TRANS_STATUS.MOBILE_CHECKING:
        return ApiJsonErrorResponse(const.API_ERROR.CONFIRM_STATUS_ERROR)

    if list_ret['user_mobile'] == safe_vars['user_mobile']:
        return ApiJsonErrorResponse(const.API_ERROR.CONFIRM_MOBILE_ERROR)

    # TODO 用验证码调用银行接口
    now = datetime.now()
    sp_bankroll_data = dict(
        list_id=safe_vars['list_id'],
        spid=list_ret['spid'],
        bankroll_type=const.SP_BANKROLL_TYPE.IN,
        status=const.TRANS_STATUS.MOBILE_CHECKING,  # 支付中
        cur_type=list_ret['cur_type'],
        bank_type=list_ret['bank_type'],
        create_time=now,
        modify_time=now,
        product_type=const.PRODUCT_TYPE.FENQI,
        list_sign=const.LIST_SIGN.WELL)

    fenle_bankroll_data = dict(
        list_id=safe_vars['list_id'],
        spid=list_ret['spid'],
        fenle_account_id=config.FENLE_ACCOUNT_NO,
        fenle_account_type=const.FENLE_ACCOUNT.VIRTUAL,  # 1真实，2虚拟
        status=const.TRANS_STATUS.MOBILE_CHECKING,  # 支付中
        bank_type=list_ret['bank_type'],
        cur_type=list_ret['cur_type'],
        bank_tid=list_ret['bank_tid'],
        bank_backid=list_ret['bank_backid'],
        create_time=now,
        modify_time=now,
        product_type=const.PRODUCT_TYPE.FENQI, )

    # fee_duty  计算手续费生成金额
    if safe_vars['fee_duty'] == const.FEE_DUTY.BUSINESS:  # 商户付手续费
        sp_bankroll_data.update({
            'pay_num': list_ret['pay_num'],
            'sp_num': list_ret['pay_num'] - list_ret['fee']
        })
        fenle_bankroll_data.update({
            'pay_num': list_ret['pay_num'],
            'fact_amount': (list_ret['pay_num'] -
                            list_ret['bank_fee']),
            'income_num': list_ret['fee'] - list_ret['bank_fee']
        })
    else:
        # 用户付手续费情形
        return ApiJsonErrorResponse(const.API_ERROR.NO_USER_PAY)
    fenle_bankroll_data.update({
        'bank_tid': list_ret['bank_tid'],
        'bank_backid': ""})

    with transaction(db) as trans:
        ret = db.execute(t_sp_bankroll_list.insert(), sp_bankroll_data)
        last_id = ret._saved_cursor._last_insert_id
        db.execute(t_fenle_bankroll_list.insert(), fenle_bankroll_data)
        trans.finish()

    # 根据银行返回信息更新余额及流水
    now = datetime.now()
    udp_sp_balance = t_sp_balance.update().where(and_(
        t_sp_balance.c.spid == list_ret['spid'],
        t_sp_balance.c.cur_type == list_ret['cur_type'])).values(
        balance=t_sp_balance.c.balance +
            list_ret['paynum'] - list_ret['fee'],
        modify_time=now)

    udp_fenle_balance = t_fenle_balance.update().where(and_(
        t_fenle_balance.c.account_no == config.FENLE_ACCOUNT_NO,
        t_fenle_balance.c.bank_type == config.FENLE_BANK_TYPE)).values(
        balance=t_fenle_balance.c.balance +
            list_ret['fee'] - list_ret['bank_fee'],
        modify_time=now)

    udp_trans_list = t_trans_list.update().where(
        t_trans_list.c.list_id == safe_vars['list_id']).values(
        status=const.TRANS_STATUS.PAY_SUCCESS,
        bank_backid='321',
        modify_time=now)

    udp_fenle_bankroll = t_fenle_bankroll_list.update().where(and_(
        t_fenle_bankroll_list.c.bank_tid == list_ret['bank_tid'],
        t_fenle_bankroll_list.c.bank_type == list_ret['bank_type']))\
        .values(status=const.TRANS_STATUS.PAY_SUCCESS, modify_time=now)

    udp_sp_bankroll = t_sp_bankroll_list.update().where(
        t_sp_bankroll_list.c.id == last_id).values(
        status=const.TRANS_STATUS.PAY_SUCCESS,
        modify_time=now)

    with transaction(db) as trans:
        db.execute(udp_sp_bankroll)
        db.execute(udp_fenle_bankroll)

        db.execute(udp_sp_balance)
        db.execute(udp_fenle_balance)
        db.execute(udp_trans_list)
        trans.finish()

    # 从mysql获取商户公钥
    s = select([t_merchant_info.c.rsa_pub_key]).where(
        t_merchant_info.c.spid == safe_vars['spid'])
    merchant_ret = db.execute(s).first()
    ret_data = dict(
        spid=list_ret['spid'],
        sp_tid=list_ret['sp_tid'],
        money=list_ret['paynum'],
        cur_type=list_ret['cur_type'],
        divided_term=list_ret['divided_term'],
        fee_duty=list_ret['fee_duty'],
        pay_type=const.PRODUCT_TYPE.FENQI,
        user_account_type=list_ret['user_account_type'],
        encode_type=safe_vars['encode_type'], )

    ret_data.update({
        "list_id": list_ret['list_id'],
        "result": list_ret['status'], })
    ret_data = util.encode_unicode(ret_data)
    cipher_data = util.rsa_sign_and_encrypt_params(
        ret_data,
        config.FENLE_PRIVATE_KEY,
        merchant_ret['rsa_pub_key'])
    return ApiJsonOkResponse(
        cipher_data=cipher_data,
        safe_vars=safe_vars,)


@home.route("/query/single")
@general("单笔查询支付接口")
@db_conn
@api_sign_and_encrypt_form_check({
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

    sel = select([t_trans_list.c.status,
                  t_trans_list.c.sp_userid,
                  t_trans_list.c.sp_tid,
                  t_trans_list.c.paynum,
                  t_trans_list.c.fee,
                  t_trans_list.c.cur_type,
                  t_trans_list.c.divided_term,
                  t_trans_list.c.fee_duty,
                  t_trans_list.c.memo,
                  t_trans_list.c.product_type,
                  t_trans_list.c.bank_type, ]).where(
        t_trans_list.c.list_id == safe_vars['list_id'])
    list_ret = db.execute(sel).first()

    if list_ret is None:
        return ApiJsonErrorResponse(const.API_ERROR.LIST_ID_NOT_EXIST)

    # 从mysql获取商户公钥
    s = select([t_merchant_info.c.rsa_pub_key]).where(
        t_merchant_info.c.spid == safe_vars['spid'])
    merchant_ret = db.execute(s).first()
    if merchant_ret is None:
        return ApiJsonErrorResponse(const.API_ERROR.SPID_NOT_EXIST)

    ret_data = dict((k, v) for k, v in list_ret.items() if k not in (
        'status', 'paynum'))
    ret_data.update({
        "sign": safe_vars["sign"],
        "encode_type": safe_vars["encode_type"],
        "spid": safe_vars['spid'],
        "bank_name": const.BANK_ID.NAMES[list_ret["bank_type"]],
        "result": list_ret["status"], })

    cipher_data = util.rsa_sign_and_encrypt_params(
        ret_data,
        config.FENLE_PRIVATE_KEY,
        merchant_ret['rsa_pub_key'])
    return ApiJsonOkResponse(
        cipher_data=cipher_data,
        safe_vars=safe_vars)

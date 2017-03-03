#!/usr/bin/env python
# -*- coding: utf-8 -*-

import operator
import hashlib
import urllib
import json
import datetime
from base64 import b64decode

from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5 as sign_PKCS1_v1_5
from Crypto.Hash import SHA
from sqlalchemy.sql import select
from sqlalchemy import and_

from base import pp_interface as pi
from base.framework import transaction
from base import constant as const
from base import util
from base.db import t_user_bank
from base.db import t_merchant_info
from base.db import t_sp_bank
from base.db import t_bank_channel
from base.db import t_trans_list
from base.db import t_sp_balance
from base.db import t_sp_history
from base.db import t_fenle_balance
from base.db import t_fenle_history
import config


def check_balance(db, account_class, spid, cur_type=const.CUR_TYPE.RMB):
    sel_sp_balance = select([t_sp_balance.c.balance]).where(and_(
        t_sp_balance.c.spid == spid,
        t_sp_balance.c.account_class == account_class,
        t_sp_balance.c.cur_type == cur_type))
    if db.execute(sel_sp_balance).first() is None:
        return False, const.API_ERROR.SP_BALANCE_NOT_EXIST
    return True, None


def check_repeat_list(db, spid, sp_list):
    """ 检查订单号是否已经存在"""
    sel = select([t_trans_list.c.id]).where(and_(
        t_trans_list.c.spid == spid,
        t_trans_list.c.sp_list == sp_list))
    list_ret = db.execute(sel).first()
    if list_ret is not None:   # 如果已经存在
        return False, const.API_ERROR.REPEAT_PAY
    return True, None


def check_user_bank(db, acc_no, bank_type, mobile, now):
    """ 检查用户银行卡信息 user_bank"""
    sel = select([t_user_bank.c.status]).where(
        t_user_bank.c.bankacc_no == acc_no)
    user_bank_ret = db.execute(sel).first()
    now = datetime.datetime.now()
    if user_bank_ret is None:
        user_bank_info = {
            'bankacc_no': acc_no,
            'account_type': const.ACCOUNT_TYPE.CREDIT_CARD,
            'bank_type': bank_type,
            'account_mobile': mobile,
            'status': const.USER_BANK_STATUS.INIT,
            'create_time': now,
            'modify_time': now}
        db.execute(t_user_bank.insert(), user_bank_info)
    else:
        # 检查银行卡是否被冻结 user_bank
        if user_bank_ret['status'] == const.USER_BANK_STATUS.FREEZING:  # 冻结标志
            return False, const.API_ERROR.ACCOUNT_FREEZED
    return True, None


def check_bank_channel(db, product, bank_type, pin_code, name, div_term):
    fee_percent = {'error_code': None}
    if product not in (const.PRODUCT.LAYAWAY, const.PRODUCT.POINT,
                       const.PRODUCT.POINT_CASH, const.PRODUCT.CONSUME):
        fee_percent['error_code'] = const.API_ERROR.PRODUCT_NOT_EXIST
        return False, fee_percent
    sel = select([t_bank_channel.c.status,
                  t_bank_channel.c.fenqi_fee_percent,
                  t_bank_channel.c.jifen_fee_percent,
                  t_bank_channel.c.cash_fee_percent,
                  t_bank_channel.c.interface_mask]).where(
        t_bank_channel.c.bank_type == bank_type)
    channel_ret = db.execute(sel).first()
    if channel_ret is None:
        fee_percent['error_code'] = const.API_ERROR.BANK_NOT_EXIST
        return False, fee_percent

    if channel_ret['status'] == const.BOOLEAN.FALSE:  # 银行渠道不可用
        fee_percent['error_code'] = const.API_ERROR.BANK_CHANNEL_UNABLE
        return False, fee_percent

    if channel_ret['interface_mask'] is not None:
        # 验证安全码
        if (channel_ret['interface_mask'] & const.PAY_MASK.PIN_CODE) and \
           (pin_code is None):
            fee_percent['error_code'] = const.API_ERROR.NO_PIN_CODE
            return False, fee_percent
        # 验证姓名
        if (channel_ret['interface_mask'] & const.PAY_MASK.NAME) and \
           (name is None):
            fee_percent['error_code'] = const.API_ERROR.NO_USER_NAME
            return False, fee_percent

    if product == const.PRODUCT.LAYAWAY:
        fenqi_fee_percent = json.loads(channel_ret['fenqi_fee_percent'])
        if str(div_term) not in fenqi_fee_percent:
            fee_percent['error_code'] = const.API_ERROR.DIV_TERM_NOT_EXIST
            return False, fee_percent
        fee_percent[product] = fenqi_fee_percent[str(div_term)]
    elif product == const.PRODUCT.POINT:
        fee_percent[product] = channel_ret['jifen_fee_percent']
    elif product == const.PRODUCT.CONSUME:
        fee_percent[product] = channel_ret['cash_fee_percent']
    else:
        fee_percent['cash'] = channel_ret['cash_fee_percent']
        fee_percent['jifen'] = channel_ret['jifen_fee_percent']
    return True, fee_percent


def check_sp_bank(db, product, spid, bank_type, div_term):
    """ 查 sp_bank 的 fenqi_fee_percent """
    fee_percent = {'error_code': None}
    if product not in (const.PRODUCT.LAYAWAY, const.PRODUCT.POINT,
                       const.PRODUCT.POINT_CASH, const.PRODUCT.CONSUME):
        fee_percent['error_code'] = const.API_ERROR.PRODUCT_NOT_EXIST
        return False, fee_percent
    sel = select([
        t_sp_bank.c.fenqi_fee_percent,
        t_sp_bank.c.jifen_fee_percent,
        t_sp_bank.c.cash_fee_percent]).where(and_(
            t_sp_bank.c.spid == spid,
            t_sp_bank.c.bank_type == bank_type))
    sp_bank_ret = db.execute(sel).first()
    if sp_bank_ret is None:
        fee_percent['error_code'] = const.API_ERROR.NO_SP_BANK
        return False, fee_percent
    if product == const.PRODUCT.LAYAWAY:
        fenqi_fee_percent = json.loads(sp_bank_ret['fenqi_fee_percent'])
        if str(div_term) not in fenqi_fee_percent:
            fee_percent['error_code'] = const.API_ERROR.DIV_TERM_NOT_EXIST
            return False, fee_percent
        fee_percent[product] = fenqi_fee_percent[str(div_term)]
    elif product == const.PRODUCT.POINT:
        fee_percent[product] = sp_bank_ret['jifen_fee_percent']
    elif product == const.PRODUCT.CONSUME:
        fee_percent[product] = sp_bank_ret['cash_fee_percent']
    else:
        fee_percent['cash'] = sp_bank_ret['cash_fee_percent']
        fee_percent['jifen'] = sp_bank_ret['jifen_fee_percent']
    return True, fee_percent


def update_sp_balance(spid, account_class, balance, now,
                      cur_type=const.CUR_TYPE.RMB):
    """return a sql without execute"""
    return t_sp_balance.update().where(and_(
        t_sp_balance.c.spid == spid,
        t_sp_balance.c.cur_type == cur_type,
        t_sp_balance.c.account_class == account_class
    )).values(
        balance=t_sp_balance.c.balance + balance,
        modify_time=now)


def get_list(db, bank_list, what_status=None):
    sel = select([
        t_trans_list.c.id,
        t_trans_list.c.status,
        t_trans_list.c.spid,
        t_trans_list.c.mobile,
        t_trans_list.c.bank_type,
        t_trans_list.c.sp_tid,
        t_trans_list.c.amount,
        t_trans_list.c.bank_fee,
        t_trans_list.c.fee,
        t_trans_list.c.cur_type,
        t_trans_list.c.div_term,
        t_trans_list.c.product,
        t_trans_list.c.modify_time,
    ]).where(
        t_trans_list.c.bank_list == bank_list)

    list_ret = db.execute(sel).first()
    if list_ret is None:
        return False, const.API_ERROR.LIST_ID_NOT_EXIST
    if what_status == const.TRANS_STATUS.PAY_SUCCESS:
        if list_ret['status'] != const.TRANS_STATUS.PAY_SUCCESS:
            return False, const.API_ERROR.LIST_STATUS_ERROR
    return True, list_ret


def get_sp_pubkey(db, spid):
    """从mysql获取商户公钥"""
    s = select([t_merchant_info.c.rsa_pub_key]).where(
        t_merchant_info.c.spid == spid)
    merchant_ret = db.execute(s).first()
    return merchant_ret['rsa_pub_key']


def check_sign_md5(db, params):
    """ TODO: 从数据库获取key分配给商户"""
    key = "123456"

    sign = params["sign"]

    params = params.items()
    params = [(k, v) for k, v in params if
              v is not None and v != "" and k != "sign"]

    params = sorted(params, key=operator.itemgetter(0))
    params_with_key = params + [("key", key)]

    urlencoded_params = urllib.urlencode(params_with_key)

    # MD5签名
    m = hashlib.md5()
    m.update(urlencoded_params)
    computed_sign = m.hexdigest()

    return sign == computed_sign


def check_sign_rsa(db, params):
    sign = params["sign"]
    sign = b64decode(sign)

    params = params.items()
    params = [(k, v) for k, v in params if
              v is not None and v != "" and k != "sign"]

    params = sorted(params, key=operator.itemgetter(0))
    urlencoded_params = urllib.urlencode(params)

    # TODO: 从数据库获取
    merchant_public_key = RSA.importKey(config.TEST_MERCHANT_PUB_KEY)
    verifier = sign_PKCS1_v1_5.new(merchant_public_key)

    h = SHA.new(urlencoded_params)

    return verifier.verify(h, sign)


def check_db_set(db, safe_vars, now, for_sms=False):
    """检查系统相关设置"""

    if not for_sms:
        # 检查订单号是否已经存在
        ok, ret_repeat = check_repeat_list(
            db, safe_vars['spid'], safe_vars['sp_list'])
        if not ok:   # 如果已经存在
            return False, ret_repeat

        # 只支持信用卡
        if safe_vars['account_type'] != const.ACCOUNT_TYPE.CREDIT_CARD:
            return False, const.API_ERROR.ACCOUNT_TYPE_ERROR

        # 只支持人民币
        if safe_vars['cur_type'] != const.CUR_TYPE.RMB:
            return False, const.API_ERROR.CUR_TYPE_ERROR

    # 检查余额账户
    ok, ret_balance = check_balance(
        db, const.ACCOUNT_CLASS.B, safe_vars['spid'])
    if not ok:
        return False, ret_balance
    ok, ret_balance = check_balance(
        db, const.ACCOUNT_CLASS.C, safe_vars['spid'])
    if not ok:
        return False, ret_balance
    ok, ret_balance = check_balance(
        db, const.ACCOUNT_CLASS.C, config.FENLE_SPID)
    if not ok:
        return False, ret_balance

    now = datetime.datetime.now()
    # 检查用户银行卡信息 user_bank
    ok, ret_user_bank = check_user_bank(
        db, safe_vars['bankacc_no'], safe_vars['bank_type'],
        safe_vars['mobile'], now)
    if not ok:
        return False, ret_user_bank
    return True, None


def trade(db, product, safe_vars):
    """ 处理逻辑"""
    now = datetime.datetime.now()

    ok, ret_db_set = check_db_set(db, safe_vars, now)
    if not ok:
        return False, ret_db_set

    if product != const.PRODUCT.LAYAWAY:
        safe_vars['div_term'] = 6
    # 检查银行渠道是否可用，
    ok, bank_fee_percent = check_bank_channel(
        db, product,
        safe_vars['bank_type'], safe_vars['pin_code'],
        safe_vars['true_name'], safe_vars['div_term'])
    if not ok:
        return False, bank_fee_percent['error_code']

    # 检查商户银行
    ok, fenle_fee_percent = check_sp_bank(
        db, product,
        safe_vars['spid'], safe_vars['bank_type'],
        safe_vars['div_term'])
    if not ok:
        return False, fenle_fee_percent

    # 生成订单相关数据
    list_data = {
        'id': util.gen_trans_id(safe_vars['spid'],
                                safe_vars['bank_type']),
        'fee_duty': const.FEE_DUTY.SP,
        'product': product,
        'channel': const.CHANNEL.API,
        'bank_list': util.gen_bank_list(),
        'status': const.TRANS_STATUS.PAYING,  # 支付中
        'create_time': now,
        'modify_time': now}

    if product == const.PRODUCT.POINT_CASH:
        list_data['bank_fee']\
            = (safe_vars['amount'] * bank_fee_percent['cash'] +
               safe_vars['jf_deduct_money'] *
               bank_fee_percent['jifen']) // 10000

        list_data['fee']\
            = (safe_vars['amount'] * fenle_fee_percent['cash'] +
               safe_vars['jf_deduct_money'] *
               bank_fee_percent['jifen']) // 10000
    else:
        list_data['bank_fee']\
            = safe_vars['amount'] * bank_fee_percent[product] // 10000
        list_data['fee']\
            = safe_vars['amount'] * fenle_fee_percent[product] // 10000

    # 更新订单字段
    list_data.update(safe_vars)
    list_data.pop('sign', None)
    list_data.pop('encode_type', None)
    # TODO 调用银行支付请求接口,更新余额
    interface_input = {
        'ver': '1.0',
        'request_type': const.PRODUCT.TRADE_REQUEST_TYPE[product]}
    for k in ('amount', 'bankacc_no', 'mobile', 'valid_date',
              'bank_sms_time', 'bank_list', 'bank_validcode',
              'bank_type'):
        interface_input[k] = list_data[k]
    if product == const.PRODUCT.LAYAWAY:
        interface_input['div_term'] = list_data['div_term']
    if product == const.PRODUCT.POINT_CASH:
        interface_input['jf_deduct_money'] = list_data['jf_deduct_money']

    ok, msg = pi.call2(interface_input)

    if not ok:
        list_data['status'] = const.TRANS_STATUS.PAY_FAIL
    else:
        list_data['status'] = const.TRANS_STATUS.PAY_SUCCESS
        list_data['bank_roll'] = msg['bank_roll']  # 填入银行返回信息
        list_data['bank_settle_time'] = msg['bank_settle_time']  # 填入银行返回信息

    db.execute(t_trans_list.insert(), list_data)

    sp_history_data = {
        'biz': const.BIZ.TRANS,
        'amount': list_data['amount'],
        'ref_str_id': list_data['id'],
        'create_time': now}
    fenle_history_data = sp_history_data.copy()

    udp_sp_balance = update_sp_balance(
        safe_vars['spid'], const.ACCOUNT_CLASS.B,
        list_data['amount'], now)
    sp_history_data.update({
        'spid': safe_vars['spid'],
        'account_class': const.ACCOUNT_CLASS.B})

    udp_fenle_balance = t_fenle_balance.update().where(and_(
        t_fenle_balance.c.bankacc_no == config.FENLE_ACCOUNT_NO,
        t_fenle_balance.c.bank_type == config.FENLE_BANK_TYPE)).values(
        balance=t_fenle_balance.c.balance + list_data['amount'],
        modify_time=now)
    fenle_history_data.update({
        'bankacc_no': config.FENLE_ACCOUNT_NO,
        'bank_type': config.FENLE_BANK_TYPE})

    udp_trans_list = t_trans_list.update().where(
        t_trans_list.c.id == list_data['id']).values(
        status=const.TRANS_STATUS.PAY_SUCCESS, modify_time=now)

    with transaction(db) as trans:
        db.execute(t_sp_history.insert(), sp_history_data)
        db.execute(udp_sp_balance)
        db.execute(t_fenle_history.insert(), fenle_history_data)
        db.execute(udp_fenle_balance)
        db.execute(udp_trans_list)
        trans.finish()

    # 返回的参数
    ret_data = {'product': product,
                'encode_type': const.ENCODE_TYPE.RSA}
    for k in ('spid', 'sp_list', 'amount', 'cur_type',
              'div_term', 'fee_duty'):
        ret_data[k] = safe_vars[k]
    sp_pubkey = get_sp_pubkey(db, safe_vars['spid'])
    ret_data.update({
        "id": list_data['id'],
        "result": const.TRANS_STATUS.PAY_SUCCESS})
    cipher_data = util.rsa_sign_and_encrypt_params(
        ret_data, config.FENLE_PRIVATE_KEY, sp_pubkey)
    return True, cipher_data

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import json

from flask import Blueprint
from sqlalchemy.sql import select, and_

from base import util
from base.framework import update_sp_balance
from base.framework import get_sp_pubkey
from base.framework import db_conn
from base.framework import general
from base.framework import ApiJsonOkResponse
from base.framework import api_form_check
from base.framework import transaction
from base.framework import ApiJsonErrorResponse
from base.xform import F_mobile, F_str, F_int, F_datetime
from base import constant as const
from base.db import t_user_bank
from base.db import t_sp_bank
from base.db import t_bank_channel
from base.db import t_fenle_history
from base.db import t_sp_history
from base.db import t_fenle_balance
from base.db import t_sp_balance
import config

home = Blueprint("home", __name__)


@home.route("/cardpay/validate")
@general("银行下发验证码")
@db_conn
@api_form_check({
    "spid": (10 <= F_str("商户号") <= 10) & "strict" & "required",
    "amount": (F_int("订单交易金额")) & "strict" & "optional",
    "bankacc_no": (F_str("付款人帐号") <= 16) & "strict" & "required",
    "mobile": (F_mobile("付款人手机号码")) & "strict" & "required",
    "bank_type": (F_str("银行代号") <= 4) & "strict" & "required",
    "expiration_date": (F_str("有效期") <= 11) & "strict" & "required",
    "sign": (F_str("签名") <= 1024) & "strict" & "required",
    "encode_type": (F_str("") <= 5) & "strict" & "required" & (
        lambda v: (v in const.ENCODE_TYPE.ALL, v)),
})
def cardpay_validate(db, safe_vars):
    """ 处理逻辑"""

    # 检查余额账户
    ret_balance = _check_balance(db, safe_vars['spid'])
    if ret_balance is not None:
        return ApiJsonErrorResponse(ret_balance)

    # 检查银行渠道是否可用
    sel = select([t_bank_channel.c.is_enable]).where(
        t_bank_channel.c.bank_type == safe_vars['bank_type'])
    channel_ret = db.execute(sel).first()
    if channel_ret is None:
        return ApiJsonErrorResponse(const.API_ERROR.BANK_NOT_EXIST)
    if channel_ret['is_enable'] == const.BOOLEAN.FALSE:  # 银行渠道不可用
        return ApiJsonErrorResponse(const.API_ERROR.BANK_CHANNEL_UNABLE)

    now = datetime.datetime.now()
    # 检查用户银行卡信息 user_bank
    ret_user_bank = _check_user_bank(
        db, safe_vars['bankacc_no'], safe_vars['bank_type'],
        safe_vars['mobile'], now)
    if ret_user_bank is not None:
        return ApiJsonErrorResponse(ret_user_bank)

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


def _check_balance(db, spid, cur_type=const.CUR_TYPE.RMB):
    sel_sp_balance = select([t_sp_balance.c.spid]).where(and_(
        t_sp_balance.c.spid == spid,
        t_sp_balance.c.cur_type == cur_type))
    if db.execute(sel_sp_balance).first() is None:
        return const.API_ERROR.SP_BALANCE_NOT_EXIST
    return None


def _check_user_bank(db, acc_no, bank_type, mobile, now):
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
            return const.API_ERROR.ACCOUNT_FREEZED
    return None


def _check_sp_bank(db, spid, bank_type, divided_term=6):
    """ 查 sp_bank 的 fenqi_fee_percent
        if not (set(safe_vars.keys()) >=
            set(('spid', 'bank_type', 'divided_term'))):
            return False, const.API_ERROR.PARAM_ERROR
    """
    sel = select([t_sp_bank.c.fenqi_fee_percent]).where(and_(
        t_sp_bank.c.spid == spid,
        t_sp_bank.c.bank_type == bank_type))
    sp_bank_ret = db.execute(sel).first()
    if sp_bank_ret is None:
        return False, const.API_ERROR.NO_SP_BANK
    fenqi_fee_percent = json.loads(sp_bank_ret['fenqi_fee_percent'])
    if str(divided_term) not in fenqi_fee_percent:
        return False, const.API_ERROR.DIVIDED_TERM_NOT_EXIST
    return True, fenqi_fee_percent

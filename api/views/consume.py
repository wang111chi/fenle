#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint

from base.framework import general
from base.framework import db_conn
from base.framework import api_form_check
from base.xform import F_mobile, F_str, F_int, F_datetime
from base import constant as const
from base.dblogic import trade_logic

home = Blueprint("home", __name__)


@home.route("/cardpay/trade")
@general("信用卡分期支付接口")
@db_conn
@api_form_check({
    "bank_sms_time": (F_str("短信下发时间") <= 32) & "strict" & "required",
    "bank_validcode": (F_str("短信验证码") <= 32) & "strict" & "required",
    "spid": (10 <= F_str("商户号") <= 10) & "strict" & "required",
    "sp_uid": (F_str("用户号") <= 20) & "strict" & "optional",
    "sp_list": (F_str("支付订单号") <= 32) & "strict" & "required",
    "amount": (F_int("订单交易金额")) & "strict" & "required",
    "notify_url": (F_str("后台回调地址") <= 255) & "strict" & "required",
    "memo": (F_str("订单备注") <= 255) & "strict" & "required",
    "attach": (F_str("附加数据") <= 255) & "strict" & "optional",
    "account_type": F_int("银行卡类型", const.ACCOUNT_TYPE.CREDIT_CARD) & (
        "strict") & "optional" & (lambda v: (v in const.ACCOUNT_TYPE.ALL, v)),
    "bankacc_no": (F_str("付款人帐号") <= 16) & "strict" & "required",
    "true_name": (F_str("付款人姓名") <= 16) & "strict" & "optional",
    "mobile": (F_mobile("付款人手机号码")) & "strict" & "required",
    "bank_type": (F_str("银行代号") <= 4) & "strict" & "required",
    "expiration_date": (F_str("有效期") <= 11) & "strict" & "required",
    "pin_code": (F_str("cvv2") <= 11) & "strict" & "optional",
    "div_term": (F_int("分期期数")) & "strict" & "required",
    "fee_duty": (F_int("手续费承担方")) & "strict" & "required" & (
        lambda v: (v in const.FEE_DUTY.ALL, v)),
    "sign": (F_str("签名") <= 1024) & "strict" & "required",
    "encode_type": (F_str("") <= 5) & "strict" & "required" & (
        lambda v: (v in const.ENCODE_TYPE.ALL, v)),
})
def cardpay_trade(db, safe_vars):
    return trade_logic(db, const.PRODUCT.LAYAWAY, safe_vars)

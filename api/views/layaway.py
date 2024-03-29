#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint

from base.framework import general, db_conn, api_form_check
from base.framework import ApiJsonOkResponse, ApiJsonErrorResponse
from base.framework import TempResponse
from base.xform import F_mobile, F_str, F_int, F_datetime
from base import constant as const
from base import dblogic as dbl
from base import util
import config


layaway = Blueprint("layaway", __name__)


@layaway.route("/layaway/trade")
@general("分期交易")
@db_conn
@api_form_check({
    "sign": (F_str("签名") <= 1024) & "strict" & "required",
    "encode_type": (F_str("签名类型") <= 5) & "strict" & "required" & (
        lambda v: (v in const.ENCODE_TYPE.ALL, v)),
    "spid": (10 <= F_str("商户号") <= 10) & "strict" & "required",
    "sp_list": (F_str("支付订单号") <= 32) & "strict" & "required",
    "true_name": (F_str("付款人姓名") <= 16) & "strict" & "optional",
    "pin_code": (F_str("cvv2") <= 11) & "strict" & "optional",
    "memo": (F_str("订单备注") <= 255) & "strict" & "optional",
    "attach": (F_str("附加数据") <= 255) & "strict" & "optional",
    "cur_type": (F_int("币种类型", const.CUR_TYPE.RMB)) & (
        "strict") & "optional" & (lambda v: (v in const.CUR_TYPE.ALL, v)),
    "account_type": F_int("银行卡类型", const.ACCOUNT_TYPE.CREDIT_CARD) & (
        "strict") & "optional" & (lambda v: (v in const.ACCOUNT_TYPE.ALL, v)),
    "bank_type": F_int("银行代号") & "strict" & "required",
    "div_term": (F_int("分期期数")) & "strict" & "required",
    "amount": (F_int("订单交易金额")) & "strict" & "required",
    "bankacc_no": (F_str("付款人帐号") <= 16) & "strict" & "required",
    "mobile": (F_mobile("付款人手机号码")) & "strict" & "required",
    "valid_date": (F_str("有效期") <= 11) & "strict" & "required",
    "bank_list": (F_str("请求银行订单号") <= 64) & "strict" & "required",
    "bank_sms_time": (F_str("短信下发时间") <= 32) & "strict" & "required",
    "bank_validcode": (F_str("短信验证码") <= 32) & "strict" & "required",
})
def trade(db, safe_vars):
    ok, msg = dbl.trade(db, const.PRODUCT.LAYAWAY, safe_vars)
    if not ok:
        return ApiJsonErrorResponse(msg)
    sp_pubkey = dbl.get_sp_pubkey(db, safe_vars['spid'])
    cipher_data = util.rsa_sign_and_encrypt_params(
        msg, config.FENLE_PRIVATE_KEY, sp_pubkey)
    return ApiJsonOkResponse(cipher_data=cipher_data)

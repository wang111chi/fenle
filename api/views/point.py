#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint

from base.framework import general, db_conn
from base.framework import api_form_check, form_check
from base.framework import ApiJsonOkResponse, ApiJsonErrorResponse
from base.framework import TempResponse
from base.xform import F_mobile, F_str, F_int, F_datetime
from base import constant as const
from base import dblogic as dbl
from base import pp_interface as pi
from base import util
import config


point = Blueprint("point", __name__)


@point.route("/point/trade")
@general("积分交易")
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
    "amount": (F_int("积分抵扣金额")) & "strict" & "required",
    "bankacc_no": (F_str("付款人帐号") <= 16) & "strict" & "required",
    "mobile": (F_mobile("付款人手机号码")) & "strict" & "required",
    "valid_date": (F_str("有效期") <= 11) & "strict" & "required",
    "bank_sms_time": (F_str("短信下发时间") <= 32) & "strict" & "required",
    "bank_validcode": (F_str("短信验证码") <= 32) & "strict" & "required",
})
def trade(db, safe_vars):
    ok, msg = dbl.trade(db, const.PRODUCT.POINT, safe_vars)
    if not ok:
        return ApiJsonErrorResponse(msg)
    sp_pubkey = dbl.get_sp_pubkey(db, safe_vars['spid'])
    cipher_data = util.rsa_sign_and_encrypt_params(
        msg, config.FENLE_PRIVATE_KEY, sp_pubkey)
    return ApiJsonOkResponse(cipher_data=cipher_data)


"""
@point.route("/point/query")
@general("积分查询")
@db_conn
@api_form_check({
    "bankacc_no": (F_str("付款人帐号") <= 16) & "strict" & "required",
    "mobile": (F_mobile("付款人手机号码")) & "strict" & "required",
    "valid_date": F_str("有效期") & "strict" & "required",
    "bank_sms_time": F_str("银行下发短信时间") & "strict" & "required",
    "bank_list": F_str("给银行订单号") & "strict" & "required",
    "bank_validcode": F_str("银行验证码") & "strict" & "required",
})
def query(db, safe_vars):
    # 调银行接口
    interface_input = {
        'ver': '1.0',
        'request_type': '2008'}
    interface_input.update(safe_vars)
    interface_input["bank_type"] = const.BANK_ID.GDB
    ok, msg = pi.call_def(interface_input)
    if not ok:
        return ApiJsonErrorResponse(msg)
    return ApiJsonOkResponse(remain_point=msg["remainJf"])
"""

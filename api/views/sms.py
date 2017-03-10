#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import json

from flask import Blueprint

from base.framework import db_conn, general, api_form_check
from base.framework import ApiJsonOkResponse, ApiJsonErrorResponse
from base.xform import F_mobile, F_str, F_int, F_datetime
from base import constant as const
from base import util
from base import dblogic as dbl
from base import pp_interface as pi
import config


sms = Blueprint("sms", __name__)


@sms.route("/sms/send")
@general("银行下发验证码")
@db_conn
@api_form_check({
    "sign": (F_str("签名") <= 1024) & "strict" & "required",
    "encode_type": (F_str("签名类型") <= 5) & "strict" & "required" & (
        lambda v: (v in const.ENCODE_TYPE.ALL, v)),
    "spid": (10 <= F_str("商户号") <= 10) & "strict" & "required",
    "true_name": (F_str("付款人姓名") <= 16) & "strict" & "optional",
    "pin_code": (F_str("cvv2") <= 11) & "strict" & "optional",
    "attach": (F_str("附加数据") <= 255) & "strict" & "optional",
    "bank_type": F_int("银行代号") & "strict" & "required",
    "amount": (F_int("订单交易金额")) & "strict" & "required",
    "bankacc_no": (F_str("付款人帐号") <= 16) & "strict" & "required",
    "mobile": (F_mobile("付款人手机号码")) & "strict" & "required",
    "valid_date": (F_str("有效期") <= 11) & "strict" & "required",
})
def send(db, safe_vars):
    now = datetime.datetime.now()

    # 检查用户银行卡信息 user_bank
    ok, error_code = dbl.check_user_bank(
        db, safe_vars['bankacc_no'], safe_vars['bank_type'],
        safe_vars['mobile'], now)
    if not ok:
        return ApiJsonErrorResponse(error_code)

    # 检查银行渠道是否可用
    ok, channel = dbl.check_bank_channel(
        db, const.PRODUCT.POINT, safe_vars['bank_type'],
        safe_vars['pin_code'], safe_vars['true_name'], div_term=6)
    if not ok:
        return ApiJsonErrorResponse(channel['error_code'])

    # 检查商户银行
    is_ok, sp_bank = dbl.check_sp_bank(
        db, const.PRODUCT.POINT, safe_vars['spid'],
        safe_vars['bank_type'], div_term=6)
    if not is_ok:
        return ApiJsonErrorResponse(sp_bank['error_code'])

    # TODO 调用银行短信下发接口
    input_data = {
        'ver': '1.0',
        'request_type': '2001',
        'bank_type': safe_vars['bank_type'],
        'bank_list': util.gen_bank_list()}
    for k in ('amount', 'bankacc_no', 'mobile', 'valid_date'):
        input_data[k] = safe_vars[k]
    ok, msg = pi.call_def(input_data)
    if not ok:
        return ApiJsonErrorResponse(msg)

    ret_data = {
        'bank_list': input_data['bank_list'],
        "bank_sms_time": msg['bank_sms_time']}  # 此处为银行返回时间
    sp_pubkey = dbl.get_sp_pubkey(db, safe_vars['spid'])
    cipher_data = util.rsa_sign_and_encrypt_params(
        ret_data, config.FENLE_PRIVATE_KEY, sp_pubkey)
    return ApiJsonOkResponse(cipher_data=cipher_data)

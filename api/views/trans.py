#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, request

from base.framework import db_conn, general
from base.framework import api_form_check
from base.framework import ApiJsonErrorResponse, ApiJsonOkResponse
from base.xform import F_mobile, F_str, F_int, F_datetime
from base import constant as const
from base import dblogic as dbl
from base import util
import config


trans = Blueprint("trans", __name__)


@trans.route("/trans/query")
@general("单笔查询接口")
@db_conn
@api_form_check({
    "sign": (F_str("签名") <= 1024) & "strict" & "required",
    "encode_type": (F_str("") <= 5) & "strict" & "required" & (
        lambda v: (v in const.ENCODE_TYPE.ALL, v)),
    "spid": (10 <= F_str("商户号") <= 10) & "strict" & "required",
    "list_id": (F_str("交易单号") <= 32) & "strict" & "required",
})
def trans_query(db, safe_vars):
    list_data = dbl.get_list(db, safe_vars['list_id'])
    if list_data is None:
        return ApiJsonErrorResponse(const.API_ERROR.LIST_ID_NOT_EXIST)
    list_data = dict(list_data)
    sp_pubkey = dbl.get_sp_pubkey(db, list_data['spid'])
    # 返回的参数
    ret_data = {'list_id': safe_vars['list_id'],
                'result': list_data['status'],
                'encode_type': const.ENCODE_TYPE.RSA}
    for k in ('spid', 'sp_list', 'amount', 'cur_type',
              'div_term', 'fee_duty', 'bank_type'):
        ret_data[k] = list_data.get(k)

    cipher_data = util.rsa_sign_and_encrypt_params(
        ret_data, config.FENLE_PRIVATE_KEY, sp_pubkey)
    return ApiJsonOkResponse(cipher_data=cipher_data)


@trans.route("/trans/refund")
@general("退款接口")
@db_conn
@api_form_check({
    "sign": (F_str("签名") <= 1024) & "strict" & "required",
    "encode_type": (F_str("") <= 5) & "strict" & "required" & (
        lambda v: (v in const.ENCODE_TYPE.ALL, v)),
    "spid": (10 <= F_str("商户号") <= 10) & "strict" & "required",
    "list_id": (F_str("交易单号") <= 32) & "strict" & "required",
    "sp_refund_id": (F_str("商户退款单号") <= 32) & "strict" & "required",
})
def refund(db, safe_vars):
    ok, msg = dbl.cancel_or_refund(db, safe_vars["list_id"])
    if not ok:
        return ApiJsonErrorResponse(msg)
    sp_pubkey = dbl.get_sp_pubkey(db, safe_vars['spid'])
    cipher_data = util.rsa_sign_and_encrypt_params(
        msg, config.FENLE_PRIVATE_KEY, sp_pubkey)
    return ApiJsonOkResponse(cipher_data=cipher_data)

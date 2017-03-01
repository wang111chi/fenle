#!/usr/bin/env python3

import datetime

from flask import Blueprint
from flask import request
import gevent
import requests

from base.framework import general, db_conn, form_check
from base.framework import JsonOkResponse, JsonErrorResponse, TempResponse
from base.db import engine
from base import util
from base import logic
from base import dblogic as dbl
from base import logger
from base.xform import F_str, F_int, F_mobile
from base import constant as const
from base import pp_interface as pi
from base.db import tables


preauth = Blueprint("preauth", __name__)


@preauth.route("/preauth")
@general("预授权页面载入")
def load():
    return TempResponse("preauth.html")


@preauth.route("/preauth/trade", methods=["POST"])
@general("预授权")
@db_conn
@form_check({
    "amount": (F_int("预授权金额")) & "strict" & "required",
    "bankacc_no": (F_str("付款人帐号") <= 16) & "strict" & "required",
    "mobile": (F_mobile("付款人手机号码")) & "strict" & "required",
    "valid_date": F_str("有效期") & "strict" & "required",
    "bank_sms_time": F_str("银行下发短信时间") & "strict" & "required",
    "bank_list": F_str("给银行订单号") & "strict" & "required",
    "bank_validcode": F_str("银行验证码") & "strict" & "required",
})
def trade(db, safe_vars):
    ok, msg = dbl.trade(db, const.PRODUCT_TYPE.PREAUTH, safe_vars)
    if not ok:
        return JsonErrorResponse(msg)
    return JsonOkResponse(trans=msg)


@preauth.route("/preauth/done", methods=["POST"])
@general("预授权完成")
@db_conn
@form_check({
    "amount": (F_int("预授权完成金额")) & "strict" & "required",
    "bankacc_no": (F_str("付款人帐号") <= 16) & "strict" & "required",
    "mobile": (F_mobile("付款人手机号码")) & "strict" & "required",
    "valid_date": F_str("有效期") & "strict" & "required",
    "bank_sms_time": F_str("银行下发短信时间") & "strict" & "required",
    "bank_list": F_str("给银行订单号") & "strict" & "required",
    "bank_validcode": F_str("银行验证码") & "strict" & "required",
    "parent_id": F_str("预授权单号") & "strict" & "required",
})
def done(db, safe_vars):
    ok, msg = dbl.trade(db, const.PRODUCT_TYPE.PREAUTH_DONE, safe_vars)
    if not ok:
        return JsonErrorResponse(msg)
    return JsonOkResponse(trans=msg)

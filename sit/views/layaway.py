#!/usr/bin/env python3

import datetime

from flask import Blueprint
from flask import request
import gevent
import requests
import sqlalchemy

import config
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


layaway = Blueprint("layaway", __name__)


@layaway.route("/layaway")
@general("分期页面载入")
def load():
    return TempResponse("layaway.html")


@layaway.route("/layaway/trade", methods=["POST"])
@general("分期交易")
@db_conn
@form_check({
    "amount": (F_int("订单交易金额")) & "strict" & "required",
    "bankacc_no": (F_str("付款人帐号") <= 16) & "strict" & "required",
    "mobile": (F_mobile("付款人手机号码")) & "strict" & "required",
    "valid_date": F_str("有效期") & "strict" & "required",
    "bank_sms_time": F_str("银行下发短信时间") & "strict" & "required",
    "bank_list": F_str("给银行订单号") & "strict" & "required",
    "div_term": F_int("分期期数") & "strict" & "required",
    "bank_validcode": F_str("银行验证码") & "strict" & "required",
})
def trade(db, safe_vars):
    ok, msg = dbl.trade(db, const.PRODUCT_TYPE.LAYAWAY, safe_vars)
    if not ok:
        return JsonErrorResponse(msg)
    return JsonOkResponse(trans_list=msg)


@layaway.route("/layaway/cancel", methods=["POST"])
@general("分期交易撤消")
@db_conn
@form_check({
    "amount": (F_int("订单交易金额")) & "strict" & "required",
    "bankacc_no": (F_str("付款人帐号") <= 16) & "strict" & "required",
    "mobile": (F_mobile("付款人手机号码")) & "strict" & "required",
    "valid_date": F_str("有效期") & "strict" & "required",
    "bank_sms_time": F_str("银行下发短信时间") & "strict" & "required",
    "bank_list": F_str("给银行订单号") & "strict" & "required",
    "div_term": F_int("分期期数") & "strict" & "required",
    "uname": F_str("开户人姓名") & "strict" & "required",
    "bank_validcode": F_str("银行验证码") & "strict" & "required",
})
def cancel(db, safe_vars):
    return JsonOkResponse()

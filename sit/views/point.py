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


point = Blueprint("point", __name__)


@point.route("/point")
@general("积分页面载入")
def load():
    return TempResponse("point.html")


@point.route("/point/trade", methods=["POST"])
@general("积分交易")
@db_conn
@form_check({
    "bank_spid": F_str("商户号", format=r"^\d{15}$") & "strict" & "required",
    "terminal_id": F_str("终端号", format=r"^\d{8}$") & "strict" & "required",
    "amount": (F_int("积分抵扣金额") >= 0) & "strict" & "required",
    "bankacc_no": F_str("付款人帐号", format=r"(^\d{16}$)|(^\d{19}$)") &
    "strict" & "required",
    "mobile": (F_mobile("付款人手机号码")) & "strict" & "required",
    "valid_date": F_str("有效期", format=r"^\d{4}$") & "strict" & "required",
    "bank_sms_time": F_str("银行下发短信时间") & "strict" & "required",
    "bank_list": F_str("给银行订单号") & "strict" & "required",
    "bank_validcode": F_str("银行验证码", format=r"^\d{6}$") &
    "strict" & "required",
})
def trade(db, safe_vars):
    ok, msg = dbl.trade(db, const.PRODUCT_TYPE.POINT, safe_vars)
    if not ok:
        return JsonErrorResponse(msg)
    return JsonOkResponse(trans=msg)


@point.route("/point/query/load")
@general("积分查询页面载入")
def query_load():
    return TempResponse("point_query.html")


@point.route("/point/query")
@general("积分查询")
@db_conn
@form_check({
    "bank_spid": F_str("商户号", format=r"^\d{15}$") & "strict" & "required",
    "terminal_id": F_str("终端号", format=r"^\d{8}$") & "strict" & "required",
    "bankacc_no": F_str("付款人帐号", format=r"(^\d{16}$)|(^\d{19}$)") &
    "strict" & "required",
    "mobile": (F_mobile("付款人手机号码")) & "strict" & "required",
    "valid_date": F_str("有效期", format=r"^\d{4}$") & "strict" & "required",
    "bank_sms_time": F_str("银行下发短信时间") & "strict" & "required",
    "bank_list": F_str("给银行订单号") & "strict" & "required",
    "bank_validcode": F_str("银行验证码", format=r"^\d{6}$") &
    "strict" & "required",
})
def query(db, safe_vars):
    # 调银行接口
    interface_input = {
        'ver': '1.0',
        'request_type': '2008',
    }

    interface_input.update(safe_vars)
    interface_input["bank_type"] = const.BANK_ID.GDB

    ok, msg = pi.call2(interface_input)
    if not ok:
        return JsonErrorResponse(msg)

    return JsonOkResponse(remain_point=msg["remainJf"],
                          deduct_money=msg["deductMoney"])

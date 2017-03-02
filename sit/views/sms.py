#!/usr/bin/env python3

import datetime

from flask import Blueprint
from flask import request
import gevent
import requests
import sqlalchemy

from base.framework import general, db_conn, form_check
from base.framework import JsonOkResponse, JsonErrorResponse, TempResponse
from base.db import engine
from base import util
from base import logic
from base import logger
from base.xform import F_str, F_int, F_mobile
from base import constant as const
from base import pp_interface as pi
from base.db import tables


sms = Blueprint("sms", __name__)


@sms.route("/sms/send", methods=["POST"])
@general("银行下发验证码")
@form_check({
    "bank_spid": (F_str("商户号") <= 16) & "strict" & "required",
    "terminal_id": (F_str("终端号") <= 16) & "strict" & "required",
    "amount": (F_int("订单交易金额")) & "strict" & "required",
    "bankacc_no": (F_str("付款人帐号") <= 16) & "strict" & "required",
    "mobile": (F_mobile("付款人手机号码")) & "strict" & "required",
    "valid_date": F_str("有效期") & "strict" & "required",
})
def send(safe_vars):
    now = datetime.datetime.now()

    # 生成给银行的订单号
    bank_list = now.strftime("%Y%m%d%H%M%S")
    bank_type = const.BANK_ID.GDB

    input_data = safe_vars
    input_data.update({
        'ver': '1.0',
        'request_type': '2001',
        'bank_list': bank_list,
        'bank_type': bank_type,
    })

    ok, msg = pi.call2(input_data)
    if not ok:
        return JsonErrorResponse(msg)

    return JsonOkResponse(
        bank_list=bank_list,
        bank_sms_time=msg["bank_sms_time"],
    )

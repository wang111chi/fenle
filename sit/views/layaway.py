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
    "amount": (F_int("订单交易金额")) & "strict" & "optional",
    "bankacc_no": (F_str("付款人帐号") <= 16) & "strict" & "required",
    "mobile": (F_mobile("付款人手机号码")) & "strict" & "required",
    "valid_date": F_str("有效期") & "strict" & "required",
    "bank_sms_time": F_str("银行下发短信时间") & "strict" & "required",
    "bank_list": F_str("给银行订单号") & "strict" & "required",
    "div_term": F_int("分期期数") & "strict" & "required",
    "bank_validcode": F_str("银行验证码") & "strict" & "required",
})
def trade(db, safe_vars):
    now = datetime.datetime.now()

    bank_type = const.BANK_ID.GDB
    trans_list_id = util.gen_trans_list_id(config.SPID, bank_type)
    t_trans_list = tables["trans_list"]

    # 生成订单
    trans_list_data = {}
    trans_list_data.update(safe_vars)
    trans_list_data.update({
        "id": trans_list_id,
        "bank_type": bank_type,
        "product": const.PRODUCT_TYPE.LAYAWAY,
        "status": const.TRANS_STATUS.DOING,
        "create_time": now,
        "modify_time": now,
    })

    try:
        trans_list_id = db.execute(
            t_trans_list.insert(),
            **trans_list_data
        ).inserted_primary_key
    except sqlalchemy.exc.IntegrityError:
        trans_list = dbl.get_trans_list_by_bank_list(
            db, safe_vars["bank_list"])

        if trans_list["status"] != const.TRANS_STATUS.FAIL:
            return JsonErrorResponse("请勿重复提交交易")

        trans_list_id = trans_list["id"]

    # 调银行接口
    interface_input = {
        'ver': '1.0',
        'request_type': '2002',
    }

    interface_input.update(safe_vars)
    interface_input["bank_type"] = bank_type

    ok, msg = pi.call2(interface_input)
    if not ok:
        db.execute(t_trans_list.update().where(
            t_trans_list.c.id == trans_list_id
        ).values(
            status=const.TRANS_STATUS.FAIL,
            modify_time=datetime.datetime.now(),
        ))

        return JsonErrorResponse(msg)

    db.execute(t_trans_list.update().where(
        t_trans_list.c.id == trans_list_id
    ).values(
        bank_roll=msg['bank_roll'],
        bank_settle_time=msg['bank_settle_time'],
        status=const.TRANS_STATUS.OK,
        modify_time=datetime.datetime.now(),
    ))

    return JsonOkResponse(
        trans_list=dbl.get_trans_list_by_id(
            db, trans_list_id))


@layaway.route("/layaway/cancel", methods=["POST"])
@general("分期交易撤消")
@db_conn
@form_check({
    "amount": (F_int("订单交易金额")) & "strict" & "optional",
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

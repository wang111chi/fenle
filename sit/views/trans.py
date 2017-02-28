#!/usr/bin/env python3

import datetime

from flask import Blueprint
from flask import request
import gevent
import requests

import config
from base.framework import general, db_conn, form_check, transaction
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


trans = Blueprint("trans", __name__)


@trans.route("/trans/list")
@general("交易单列表页载入")
def list_load():
    return TempResponse("trans_list.html")


@trans.route("/trans/list/data")
@general("交易单列表页数据")
@db_conn
def list_data(db):
    t_trans_list = tables["trans_list"]
    trans_list = [dict(item) for item in
                  db.execute(t_trans_list.select()).fetchall()]
    return JsonOkResponse(rows=trans_list)


@trans.route("/trans")
@general("交易单详情")
@db_conn
@form_check({
    "bank_list": F_str("给银行订单号") & "strict" & "required",
})
def show(db, safe_vars):
    return JsonOkResponse(
        trans=dbl.get_trans_by_bank_list(db, safe_vars["bank_list"]))


@trans.route("/trans/cancel", methods=["POST"])
@general("交易撤消")
@db_conn
@form_check({
    "bank_list": F_str("给银行订单号") & "strict" & "required",
})
def cancel(db, safe_vars):
    ok, msg = _cancel_or_refund(db, safe_vars["bank_list"])
    if not ok:
        return JsonErrorResponse(msg)

    return JsonOkResponse()


@trans.route("/trans/refund", methods=["POST"])
@general("交易退货")
@db_conn
@form_check({
    "bank_list": F_str("给银行订单号") & "strict" & "required",
})
def refund(db, safe_vars):
    ok, msg = _cancel_or_refund(db, safe_vars["bank_list"], is_refund=True)
    if not ok:
        return JsonErrorResponse(msg)

    return JsonOkResponse()


def _cancel_or_refund(db, bank_list, is_refund=False):
    trans_list = dbl.get_trans_by_bank_list(db, bank_list)
    if trans_list is None:
        return False, "交易单不存在"
    if trans_list["status"] != const.TRANS_STATUS.OK:
        return False, "交易单状态不允许退货"

    t_refund_list = tables["refund_list"]

    # 生成退款单
    now = datetime.datetime.now()
    refund_id = util.gen_trans_list_id(config.SPID, trans_list["bank_type"])
    bank_refund_list = now.strftime("%Y%m%d%H%M%S")
    db.execute(
        t_refund_list.insert(),
        id=refund_id,
        bank_list=bank_refund_list,
        trans_id=trans_list["id"],
        mode=const.REFUND.MODE.REFUND if is_refund else
        const.REFUND.MODE.CANCEL,
        status=const.REFUND.STATUS.DOING,
        create_time=now,
        modify_time=now,
    )

    interface_input = {
        "ver": "1.0",
        "request_type":
        const.PRODUCT_TYPE.REFUND_REQUEST_TYPE[trans_list["product"]] if
        is_refund else
        const.PRODUCT_TYPE.CANCEL_REQUEST_TYPE[trans_list["product"]],
        "bank_refund_list": bank_refund_list,
    }

    for param in (
            "bank_type",
            "valid_date",
            "bankacc_no",
            "amount",
            "jf_deduct_money",
            "bank_roll",
            "bank_settle_time",
            "bank_list",
    ):
        interface_input[param] = trans_list[param]

    ok, msg = pi.call2(interface_input)
    if not ok:
        db.execute(t_refund_list.update().where(
            t_refund_list.c.id == refund_id
        ).values(
            status=const.TRANS_STATUS.FAIL,
            modify_time=datetime.datetime.now(),
        ))

        return False, msg

    t_trans_list = tables["trans_list"]
    with transaction(db) as trans:
        db.execute(t_refund_list.update().where(
            t_refund_list.c.id == refund_id
        ).values(
            status=const.TRANS_STATUS.OK,
            modify_time=datetime.datetime.now(),
        ))

        db.execute(t_trans_list.update().where(
            t_trans_list.c.bank_list == bank_list
        ).values(
            status=const.TRANS_STATUS.REFUND if
            is_refund else const.TRANS_STATUS.CANCEL,
            refund_id=refund_id,
            modify_time=datetime.datetime.now(),
        ))

        trans.finish()

    return True, ""

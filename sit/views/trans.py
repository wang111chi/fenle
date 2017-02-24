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

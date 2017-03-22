import datetime
import json
import gevent

from flask import Blueprint

import config
from base.framework import db_conn, general, api_form_check
from base.framework import ApiJsonOkResponse, ApiJsonErrorResponse
from base.xform import F_mobile, F_str, F_int, F_datetime
from base import constant as const
from base import util
from base import dblogic as dbl
from base import pp_interface as pi
from base.framework import transaction


test = Blueprint("test", __name__)


@test.route("/test")
@general("空测试")
def index():
    return ApiJsonOkResponse()


@test.route("/test/slow")
@general("睡2秒")
def slow():
    gevent.sleep(2)
    return ApiJsonOkResponse()


@test.route("/test/mysql/slow")
@general("MySQL查询2秒")
@db_conn
def mysql_slow(db):
    db.execute("SELECT sleep(2)")
    return ApiJsonOkResponse()


@test.route("/test/wrong/update")
@general("错误的更新方法(未加锁)")
@db_conn
def wrong_update(db):
    r = db.execute("select * from test_balance where id=1")
    balance = r.first()
    if balance["balance"] >= 10:
        db.execute("select sleep(2)")
        db.execute("update test_balance set balance=balance-10")
    return ApiJsonOkResponse()


@test.route("/test/right/update")
@general("正确的更新方法(加锁)")
@db_conn
def right_update(db):
    with transaction(db) as trans:
        r = db.execute("select * from test_balance where id=1 for update")
        balance = r.first()
        if balance["balance"] >= 10:
            db.execute("select sleep(2)")
            db.execute("update test_balance set balance=balance-10 where id=1")
        trans.finish()
    return ApiJsonOkResponse()

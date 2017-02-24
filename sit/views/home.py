#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

from flask import Blueprint, redirect
from flask import request
import gevent
import requests

from base.framework import general, db_conn, form_check
from base.framework import JsonOkResponse, TempResponse
from base.db import engine, tables
from base import util
from base import logic
from base import logger
from base.xform import F_str, F_int
from base import constant as const

home = Blueprint("home", __name__)


@home.route("/")
@general("首页")
def index():
    return redirect("/point")


@home.route("/trans_list")
@general("交易单列表")
@db_conn
def trans_list(db):
    t_trans_list = tables["trans_list"]
    trans_list = [dict(item) for item in
                  db.execute(t_trans_list.select()).fetchall()]
    return JsonOkResponse(trans_list=trans_list)

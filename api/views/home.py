#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint
from sqlalchemy.sql import text

from base.framework import db_conn
from base.framework import general
from base.framework import JsonResponse


home = Blueprint("home", __name__)


@home.route("/")
@general("首页")
def index():
    return "What do you want?"


@home.route("/cardpay/apply")
@general("信用卡分期支付申请")
def cardpay_apply():
    return JsonResponse(hello="world")

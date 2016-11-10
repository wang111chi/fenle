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
@db_conn
def index(db):
    s = text("SELECT pg_sleep(5)")
    db.execute(s)
    return "Hello, Jidui!"


@home.route("/test")
@general("测试")
def test():
    return JsonResponse(hello="world")

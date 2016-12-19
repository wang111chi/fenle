#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint

from base.framework import general
from base.framework import db_conn

home = Blueprint("home", __name__)

@home.route("/")
@general("首页")
@db_conn
def callback(db):
    return "hello callback!"

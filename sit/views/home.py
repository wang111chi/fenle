#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

from flask import Blueprint
from flask import request
import gevent
import requests

from base.framework import general, db_conn, form_check
from base.framework import JsonOkResponse, TempResponse
from base.db import engine
from base import util
from base import logic
from base import logger
from base.xform import F_str, F_int
from base import constant as const

home = Blueprint("home", __name__)


@home.route("/")
@general("首页")
def index():
    return TempResponse("index.html")

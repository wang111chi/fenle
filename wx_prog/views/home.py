#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

from flask import Blueprint
from flask import request
import gevent
import requests

from base.framework import general, db_conn, form_check, JsonOkResponse
from base.db import engine, t_callback_url
from base import util
from base import logic
from base import logger
from base import constant as const

home = Blueprint("home", __name__)


@home.route("/")
def index():
    return "Hello, wx prog!"

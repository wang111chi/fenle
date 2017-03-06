#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, redirect

from base.framework import general

home = Blueprint("home", __name__)


@home.route("/")
@general("首页")
def index():
    return redirect("/point")

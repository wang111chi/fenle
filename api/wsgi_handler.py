#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import gevent.monkey
gevent.monkey.patch_all()

import os
import sys

project_home = os.path.realpath(__file__)
project_home = os.path.split(project_home)[0]

sys.path.insert(0, os.path.split(project_home)[0])
sys.path.insert(0, project_home)

from flask import Flask
from flask import url_for, redirect

import config
from init_app import init


app = Flask(__name__)
init(app)

# route setting
import views

for name in views.__all__:
    module = __import__('views.%s' % name, fromlist=[name])
    app.register_blueprint(getattr(module, name))


if __name__ == '__main__':
    app.run(host='0.0.0.0',
            port=config.DEBUG_PORT)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# put common default settings shared by all applications here

DEBUG = True
ENCODING = 'utf8'
DEBUG_PORT = 5000
HOME_URL = 'http://www.jidui.com/'
DATABASE_URL = 'postgresql+pg8000://postgres:123456@postgres/jidui'

# Logging配置
LOGGING_CONFIG = [
    ["cgi-log", "cgi.log", "debug"],
    ["response-log", "response.log", "debug"],
]

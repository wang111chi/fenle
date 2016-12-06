#!/usr/bin/env python
# -*- coding: utf-8 -*-

# put common default settings shared by all applications here

DEBUG = True
ENCODING = 'utf8'
DEBUG_PORT = 5000
HOME_URL = 'http://www.fenle.com/'
DATABASE_URL = 'mysql+mysqlconnector://root:123456@mysql:3306/fenle_fenqi_db'

# Logging配置
LOGGING_CONFIG = [
    ["cgi-log", "cgi.log", "debug"],
    ["response-log", "response.log", "debug"],
]

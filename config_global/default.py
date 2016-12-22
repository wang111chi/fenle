#!/usr/bin/env python
# -*- coding: utf-8 -*-

# put common default settings shared by all applications here

from base import constant as const

DEBUG = True
ENCODING = 'utf8'
DEBUG_PORT = 5000
HOME_URL = 'http://www.fenle.com/'
DATABASE_URL = 'mysql+mysqlconnector://root:123456@mysql:3306/fenle_fenqi_db'

# Logging配置
LOGGING_CONFIG = [
    ["cgi-log", "cgi.log", "debug"],
    ["response-log", "response.log", "debug"],

    ["tools-log", "tools.log", "debug"],
]

# URL回调的设置，k, v的形式，其中：
# k代表模式，见 const.CALLBACK_URL.MODE
# v为一个tuple，每一项依次代表失败后多少秒执行一次新的重试
CALLBACK_URL = {
    const.CALLBACK_URL.MODE.CARDPAY_APPLY_SUCCESS_NOTIFY: (1, 30, 90, 180)
}

#!/usr/bin/env python
# -*- coding:utf-8 -*-

# put application's specific default settings here

from base import constant as const

# URL回调的设置，k, v的形式，其中：
# k代表模式，见 const.CALLBACK_URL.MODE
# v为一个tuple，每一项依次代表失败后多少秒执行一次新的重试
CALLBACK_URL = {
    const.CALLBACK_URL.MODE.CARDPAY: (1, 30, 90, 180)
}

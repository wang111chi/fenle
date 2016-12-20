#!/usr/bin/env python
# -*- coding: utf-8 -*-


class BOOLEAN(object):
    FALSE = 0
    TRUE = 1

    ALL = (FALSE, TRUE)


class REQUEST_STATUS(object):
    SUCCESS = 0                        # 请求成功
    FAIL = 1                           # 请求失败


class API_ERROR(object):
    MERCHANT_NOT_EXIST = 207200
    DECRYPT_ERROR = 207266
    PARAM_ERROR = 207001
    SIGN_INVALID = 207267

    NAMES = {
        MERCHANT_NOT_EXIST: u"商户不存在",
        DECRYPT_ERROR: u"解密失败",

        PARAM_ERROR: u"参数格式错误",
        SIGN_INVALID: u"校验签名失败",
    }


class ENCODE_TYPE(object):
    u"""签名类型"""

    MD5 = "MD5"
    RSA = "RSA"

    ALL = (MD5, RSA)


class HTTP_METHOD(object):
    u"""HTTP 请求方法"""

    GET = 0
    POST = 1
    ALL = (GET, POST)


class CALLBACK_URL(object):
    u"""URL回调相关常量"""

    class MODE(object):
        CARDPAY_APPLY_SUCCESS_NOTIFY = 1    # 分期支付API请求成功回调

        ALL = (
            CARDPAY_APPLY_SUCCESS_NOTIFY,
        )

    class STATUS(object):
        INIT = 0    # 待处理(还未回调过)
        PENDING = 1 # 待重试(需要下一次重试)
        DONE = 2    # 回调成功(不再需要重试)
        FAIL = 3    # 回调失败(重试次数已达到，同样不再需要重试)

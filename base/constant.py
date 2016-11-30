#!/usr/bin/env python
# -*- coding: utf-8 -*-


class ERROR(object):
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

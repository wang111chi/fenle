#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base64 import b64decode
import urlparse
import operator
import hashlib
import urllib

from flask import Blueprint
from sqlalchemy.sql import text
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Signature import PKCS1_v1_5 as sign_PKCS1_v1_5
from Crypto.Hash import SHA

from base.framework import db_conn
from base.framework import general
from base.framework import JsonResponse, JsonErrorResponse
from base.framework import sign_and_encrypt_form_check
from base.xform import F_mobile, F_str, F_int
from base import constant as const
from base import logger
from base import util
from base.db import engine
from base.xform import FormChecker
import config

home = Blueprint("home", __name__)


@home.route("/")
@general("首页")
#@db_conn
def index():
    return "What do you want?"


@home.route("/cardpay/apply")
@general("信用卡分期支付申请")
@sign_and_encrypt_form_check(engine.connect(), {
    "spid":
    (10 <= F_str("商户号") <= 10) & "strict" & "required",

    "sign":
    (F_str("签名") <= 1024) & "strict" & "required",

    "encode_type":
    (F_str("签名类型") <= 5) & "strict" & "required" & (
        lambda v: (v in const.ENCODE_TYPE.ALL, v)),
})
def cardpay_apply(safe_vars):
    # 处理逻辑

    ret_data = {
        "spid": "1" * 10,
        "spbillno": "12343434",
        "encode_type": const.ENCODE_TYPE.RSA,
    }

    cipher_data = util.rsa_sign_and_encrypt_params(
        ret_data,
        config.FENLE_PRIVATE_KEY,
        config.TEST_MERCHANT_PUB_KEY
    )

    return JsonResponse(
        retcode=0,
        retmsg=u"成功",
        cipher_data=cipher_data
    )

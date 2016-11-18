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
from base.framework import form_check, gen_json_error_response
from base.xform import F_mobile, F_str, F_int
from base import constant as const
from base import logger
from base import util
from base.xform import FormChecker
import config
from base.db import t_users

home = Blueprint("home", __name__)


@home.route("/")
@general("首页")
@db_conn
def index(db):
    ins = t_users.insert().values(name=u'张三')
    db.execute(ins)
    return "What do you want?"


@home.route("/cardpay/apply")
@general("信用卡分期支付申请")
@form_check({
    "cipher_data": F_str("签名加密串") & "strict" & "required",
}, error_handler=lambda msg: gen_json_error_response(
    const.ERROR.DECRYPT_ERROR))
def cardpay_apply(safe_vars):
    cipher_data = safe_vars["cipher_data"]

    # RSA解密
    try:
        cipher_data = b64decode(cipher_data)
    except ValueError:
        return gen_json_error_response(const.ERROR.DECRYPT_ERROR)

    jidui_private_key = RSA.importKey(config.JIDUI_PRIVATE_KEY)
    cipher = PKCS1_v1_5.new(jidui_private_key)

    message = util.pkcs_decrypt(cipher, cipher_data)

    if message is None:
        return gen_json_error_response(const.ERROR.DECRYPT_ERROR)

    # 参数检查
    params = urlparse.parse_qs(message)

    settings = {
        ("spid", const.ERROR.SPID_PARAM_ERROR):
        (10 <= F_str("商户号") <= 10) & "strict" & "required",

        ("sign", const.ERROR.SIGN_PARAM_ERROR):
        (F_str("签名") <= 1024) & "strict" & "required",

        ("encode_type", const.ERROR.ENCODE_TYPE_PARAM_ERROR):
        (F_str("签名类型") <= 5) & "strict" & "required" & (
            lambda v: (v in const.ENCODE_TYPE.ALL, v)),

    }

    form_settings = dict((k[0], v) for k, v in settings.iteritems())
    error_map = dict((k[0], k[1]) for k in settings.keys())
    check_keys = error_map.keys()

    req_data = {}
    for k, v in form_settings.iteritems():
        param = params.get(k, None)
        if v.multiple:
            req_data[k] = [] if param is None else param
        else:
            req_data[k] = None if param is None else param[0]

    checker = FormChecker(req_data, form_settings)
    valid_data = checker.get_valid_data()
    if not checker.is_valid():
        for key in check_keys:
            if key not in valid_data:
                return gen_json_error_response(error_map[key])

    # 验签
    encode_type = valid_data["encode_type"]
    if encode_type == const.ENCODE_TYPE.MD5:
        check_sign_valid = check_sign_md5(valid_data)
    elif encode_type == const.ENCODE_TYPE.RSA:
        check_sign_valid = check_sign_rsa(valid_data)

    if not check_sign_valid:
        return gen_json_error_response(const.ERROR.SIGN_INVALID)

    # 处理逻辑

    ret_data = {
        "spid": "1" * 10,
        "spbillno": "12343434",
        "encode_type": const.ENCODE_TYPE.RSA,
    }

    cipher_data = util.rsa_sign_and_encrypt_params(
        ret_data,
        config.JIDUI_PRIVATE_KEY,
        config.TEST_MERCHANT_PUB_KEY
    )

    return JsonResponse(
        retcode=0,
        retmsg=u"成功",
        cipher_data=cipher_data
    )


def check_sign_md5(params):
    # 分配给商户的key
    key = "123456"

    sign = params["sign"]

    params = params.items()
    params = [(k, v) for k, v in params if
              v is not None and v != "" and k != "sign"]

    params = sorted(params, key=operator.itemgetter(0))
    params_with_key = params + [("key", key)]

    urlencoded_params = urllib.urlencode(params_with_key)

    # MD5签名
    m = hashlib.md5()
    m.update(urlencoded_params)
    computed_sign = m.hexdigest()

    return sign == computed_sign


def check_sign_rsa(params):
    sign = params["sign"]
    sign = b64decode(sign)

    params = params.items()
    params = [(k, v) for k, v in params if
              v is not None and v != "" and k != "sign"]

    params = sorted(params, key=operator.itemgetter(0))
    urlencoded_params = urllib.urlencode(params)

    merchant_public_key = RSA.importKey(config.TEST_MERCHANT_PUB_KEY)
    verifier = sign_PKCS1_v1_5.new(merchant_public_key)

    h = SHA.new(urlencoded_params)

    return verifier.verify(h, sign)

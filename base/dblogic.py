#!/usr/bin/env python
# -*- coding: utf-8 -*-

import operator
import hashlib
import urllib
from base64 import b64decode

from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5 as sign_PKCS1_v1_5
from Crypto.Hash import SHA

import config
from base.db import tables


def check_sign_md5(db, params):
    # 分配给商户的key
    # TODO: 从数据库获取
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


def check_sign_rsa(db, params):
    sign = params["sign"]
    sign = b64decode(sign)

    params = params.items()
    params = [(k, v) for k, v in params if
              v is not None and v != "" and k != "sign"]

    params = sorted(params, key=operator.itemgetter(0))
    urlencoded_params = urllib.urlencode(params)

    # TODO: 从数据库获取
    merchant_public_key = RSA.importKey(config.TEST_MERCHANT_PUB_KEY)
    verifier = sign_PKCS1_v1_5.new(merchant_public_key)

    h = SHA.new(urlencoded_params)

    return verifier.verify(h, sign)


def get_trans_list_by_bank_list(db, bank_list):
    t_trans_list = tables["trans_list"]
    return db.execute(t_trans_list.select().where(
        t_trans_list.c.bank_list == bank_list)).fetchone()


def get_trans_list_by_id(db, id_):
    t_trans_list = tables["trans_list"]
    return db.execute(t_trans_list.select().where(
        t_trans_list.c.id == id_)).fetchone()

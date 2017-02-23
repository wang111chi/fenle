#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import operator
import hashlib
import urllib
from base64 import b64decode

from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5 as sign_PKCS1_v1_5
from Crypto.Hash import SHA
import sqlalchemy

import config
from base.db import tables
from base import constant as const
from base import util
from base import pp_interface as pi


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


def trade(db, product_type, safe_vars):
    now = datetime.datetime.now()

    bank_type = const.BANK_ID.GDB
    trans_list_id = util.gen_trans_list_id(config.SPID, bank_type)
    t_trans_list = tables["trans_list"]

    # 生成订单
    trans_list_data = {}
    trans_list_data.update(safe_vars)
    trans_list_data.update({
        "id": trans_list_id,
        "bank_type": bank_type,
        "product": product_type,
        "status": const.TRANS_STATUS.DOING,
        "create_time": now,
        "modify_time": now,
    })

    try:
        db.execute(
            t_trans_list.insert(),
            **trans_list_data
        )
    except sqlalchemy.exc.IntegrityError:
        trans_list = get_trans_list_by_bank_list(
            db, safe_vars["bank_list"])

        if trans_list["status"] != const.TRANS_STATUS.FAIL:
            return False, "请勿重复提交交易"

        trans_list_id = trans_list["id"]

    # 调银行接口

    interface_input = {
        'ver': '1.0',
        'request_type': const.PRODUCT_TYPE.REQUEST_TYPE[product_type],
    }

    interface_input.update(safe_vars)
    interface_input["bank_type"] = bank_type

    ok, msg = pi.call2(interface_input)
    if not ok:
        db.execute(t_trans_list.update().where(
            t_trans_list.c.id == trans_list_id
        ).values(
            status=const.TRANS_STATUS.FAIL,
            modify_time=datetime.datetime.now(),
        ))

        return False, msg

    db.execute(t_trans_list.update().where(
        t_trans_list.c.id == trans_list_id
    ).values(
        bank_roll=msg['bank_roll'],
        bank_settle_time=msg['bank_settle_time'],
        status=const.TRANS_STATUS.OK,
        modify_time=datetime.datetime.now(),
    ))

    return True, get_trans_list_by_id(db, trans_list_id)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import datetime
from decimal import Decimal
import operator
import urllib
import socket
import struct
import hashlib
from base64 import b64encode
from base64 import b64decode

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Signature import PKCS1_v1_5 as sign_PKCS1_v1_5
from Crypto.Hash import SHA
from base import db

import config
from base import constant as const


def check_sign_md5(key, params):
    # 分配给商户的key

    sign = params.pop("sign")[0]

    params = params.items()
    params = ((k, v) for k, vs in params for v in vs if v != "")

    params = sorted(params, key=operator.itemgetter(0))
    params_with_key = params + [("key", key)]

    urlencoded_params = urllib.parse.urlencode(params_with_key)

    # MD5签名
    m = hashlib.md5()
    m.update(urlencoded_params.encode())
    computed_sign = m.hexdigest()

    return sign == computed_sign


def check_sign_rsa(pub_key, params):
    sign = params.pop("sign")[0]
    sign = b64decode(sign)

    params = params.items()
    params = ((k, v) for k, vs in params for v in vs if v != "")

    params = sorted(params, key=operator.itemgetter(0))
    urlencoded_params = urllib.parse.urlencode(params)

    merchant_public_key = RSA.importKey(pub_key)
    verifier = sign_PKCS1_v1_5.new(merchant_public_key)

    h = SHA.new(urlencoded_params)

    return verifier.verify(h, sign)


def safe_json_default(obj):
    if isinstance(obj, datetime.datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(obj, datetime.date):
        return obj.strftime("%Y-%m-%d")
    elif isinstance(obj, Decimal):
        return float(obj)

    return str(obj)


def safe_json_dumps(obj, encoding=None, silent=True):
    """
    Encode a Python object to JSON formatted string.

    @params object: Python object
    @params encoding: the character encoding for str instances,
                      default is UTF-8.
    @params silent: not raise error, default is True

    @return: a JSON formatted string if dumps success or None

    """
    kwargs = {"default": safe_json_default}
    if encoding is not None:
        kwargs["encoding"] = encoding

    try:
        str = json.dumps(obj, **kwargs)
    except (ValueError, TypeError):
        if silent:
            return None
        raise

    return str


def safe_inet_ntoa(n):
    """
    Convert numerical ip to string ip.

    (like: 2071801890 -> "123.125.48.34"), return None if failed.
    """
    try:
        ip = socket.inet_ntoa(struct.pack(">L", n))
    except (struct.error, socket.error):
        return None

    return ip


def safe_inet_aton(ip):
    """
    Convert string ip to numerical ip.

    (like: "123.125.48.34" -> 2071801890), return None if failed.
    """
    try:
        n = struct.unpack(">L", socket.inet_pton(socket.AF_INET, ip))[0]
    except (struct.error, socket.error, AttributeError, TypeError):
        return None

    return n


def pkcs_encrypt(cipher, message):
    message = message.encode()
    handled = 0
    ciphertext = b""
    while len(message[handled:]) > 0:
        part = message[handled:handled + 117]
        ciphertext += cipher.encrypt(part)
        handled += len(part)
    return ciphertext


def pkcs_decrypt(cipher, ciphertext):
    e = Exception()
    handled = 0
    message = b""
    while len(ciphertext[handled:]) > 0:
        part = ciphertext[handled:handled + 128]
        try:
            m = cipher.decrypt(part, e)
        except ValueError:
            return None

        if isinstance(m, Exception):
            return None

        message += m
        handled += len(part)
    return message.decode()


def rsa_sign(message, private_key):
    u"""用SHA1 hash后再用RSA签名."""
    message = message.encode()
    h = SHA.new(message)
    private_key = RSA.importKey(private_key)
    signer = sign_PKCS1_v1_5.new(private_key)
    return signer.sign(h)


def rsa_encrypt(message, public_key):
    public_key = RSA.importKey(public_key)
    cipher = PKCS1_v1_5.new(public_key)
    return pkcs_encrypt(cipher, message)


def rsa_decrypt(cipher_data, private_key):
    """ RSA解密 """
    try:
        safe_data = b64decode(cipher_data)
    except ValueError:
        return const.API_ERROR.DECRYPT_ERROR
    merchant_private_key = RSA.importKey(private_key)
    cipher = PKCS1_v1_5.new(merchant_private_key)
    message = pkcs_decrypt(cipher, safe_data)
    if message is None:
        return const.API_ERROR.DECRYPT_ERROR
    params = urllib.parse.parse_qs(message)
    return params


def rsa_sign_and_encrypt_params(params, private_key, public_key):
    params = params.items()
    params = [(k, v) for k, v in params if
              v is not None and v != ""]
    handled_params = sorted(params, key=operator.itemgetter(0))

    sign = b64encode(rsa_sign(urllib.parse.urlencode(handled_params),
                              private_key))
    params_with_sign = handled_params + [("sign", sign)]
    urlencoded_params = urllib.parse.urlencode(params_with_sign)
    return b64encode(rsa_encrypt(urlencoded_params, public_key)).decode()


def _gen_seq_by_redis(key, expire):
    lua = """
      local current
      current = redis.call("incr",KEYS[1])
      if tonumber(current) == 1 then
        redis.call("expire",KEYS[1],%d)
      end
      return current
    """ % expire

    redis = db.get_redis()
    script = redis.register_script(lua)
    return script(keys=[key], args=[])


def gen_trans_list_id(spid, bank_type):
    u"""生成交易单ID.

    10位的spid+4位银行类型+8位日期+8位序列号

    @param<spid>: 商户号
    @param<bank_type>: 银行类型
    """
    key_prefix = "%s%s%s" % (spid,
                             bank_type,
                             datetime.date.today().strftime("%Y%m%d"))

    key = "trans_list_id:%s" % key_prefix
    return ("%s%08d" % (key_prefix,
                        _gen_seq_by_redis(key, 60 * 60 * 24 + 60)))[:30]


def gen_refund_id(spid, bank_type):
    u"""生成退款单ID.

    10位的spid+4位银行类型+8位日期+8位序列号

    @param<spid>: 商户号
    @param<bank_type>: 银行类型
    """
    key_prefix = "%s%s%s" % (spid,
                             bank_type,
                             datetime.date.today().strftime("%Y%m%d"))

    key = "refund_id:%s" % key_prefix
    return ("%s%08d" % (key_prefix,
                        _gen_seq_by_redis(key, 60 * 60 * 24 + 60)))[:30]


def gen_bank_tid(bank_spid):
    u"""生成给银行的订单号.

    15位的银行子商户号+8位日期+6位时间+6位自增序列号

    @param<bank_spid>: 银行子商户号
    """
    key_prefix = "%s%s" % (bank_spid,
                           datetime.datetime.now().strftime("%Y%m%d%H%M%S"))

    key = "bank_tid:%s" % key_prefix
    return ("%s%06d" % (key_prefix, _gen_seq_by_redis(key, 1)))[:35]


class FileLock:
    def __init__(self, file_name, path):
        self._file = os.path.join(path, file_name)
        self._fd = None
        self._locked = False

    def lock(self):
        import fcntl
        if self._locked:
            return True

        fd = open(self._file, 'a+b')
        try:
            fcntl.flock(fd.fileno(), fcntl.LOCK_NB | fcntl.LOCK_EX)
        except IOError:
            fd.close()
            return False

        self._fd = fd
        self._locked = True
        return True

    def release(self):
        import fcntl
        if self._locked:
            fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN)
            self._fd.close()
            self._fd = None
            self._locked = False

    def __del__(self):
        self.release()


def show_app(app):
    for rule in app.url_map.iter_rules():
        endpoint = rule.endpoint
        try:
            m, f = endpoint.split(".")
        except:
            continue
        handler = getattr(
            __import__('views.' + m, globals(), locals(), [f]), f)
        print(rule.rule)
        print(list(rule.methods & {"POST", "GET"})[0])
        print(handler.desc)
        print()

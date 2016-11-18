#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import datetime
from decimal import Decimal
import operator
import urllib
from base64 import b64encode

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Signature import PKCS1_v1_5 as sign_PKCS1_v1_5
from Crypto.Hash import SHA

import config


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
    @params encoding: the character encoding for str instances, default is UTF-8.
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


def to_unicode(data, encoding="utf-8", only_str=False):
    """convert data from some encoding to unicode
    data could be string, list, tuple or dict
    that contains string as key or value
    """
    if data is None:
        return unicode('')

    if isinstance(data, unicode):
        return data

    if isinstance(data, (list, tuple)):
        u_data = []
        for item in data:
            u_data.append(to_unicode(item, encoding, only_str))
        return u_data
    elif isinstance(data, dict):
        u_data = {}
        for key in data:
            u_data[to_unicode(key, encoding, only_str)] = to_unicode(
                data[key], encoding, only_str)
        return u_data
    elif isinstance(data, str):
        u_data = unicode(data, encoding, 'ignore')
    else:
        u_data = data

    if only_str:
        return u_data

    return unicode(u_data)


def pkcs_encrypt(cipher, message):
    handled = 0
    ciphertext = ""
    while len(message[handled:]) > 0:
        part = message[handled:handled + 117]
        ciphertext += cipher.encrypt(part)
        handled += len(part)
    return ciphertext


def pkcs_decrypt(cipher, ciphertext):
    e = Exception()
    handled = 0
    message = ""
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
    return message


def rsa_sign(message, private_key):
    u"""用SHA1 hash后再用RSA签名"""

    h = SHA.new(message)
    private_key = RSA.importKey(private_key)
    signer = sign_PKCS1_v1_5.new(private_key)
    return signer.sign(h)


def rsa_encrypt(message, public_key):
    public_key = RSA.importKey(public_key)
    cipher = PKCS1_v1_5.new(public_key)
    return pkcs_encrypt(cipher, message)


def rsa_sign_and_encrypt_params(params, private_key, public_key):
    params = params.items()
    params = [(k, v) for k, v in params if
              v is not None and v != ""]
    handled_params = sorted(params, key=operator.itemgetter(0))

    sign = b64encode(rsa_sign(urllib.urlencode(handled_params), private_key))
    params_with_sign = handled_params + [("sign", sign)]
    urlencoded_params = urllib.urlencode(params_with_sign)
    return b64encode(rsa_encrypt(urlencoded_params, public_key))

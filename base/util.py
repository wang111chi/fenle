#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import datetime
from decimal import Decimal


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

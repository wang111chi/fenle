#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

import socket
import urllib
from werkzeug.datastructures import MultiDict

from base import constant as const


def call(params, host='172.18.0.1', port=31001):
    u"""与前置机通讯调用银行接口.

    @param<params>: 需要发的参数，字典形式
    @param<host>: 前置机服务主机地址
    @param<port>: 前置机服务端口

    @return: 返回值是字典形式
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.sendall(_pack_params(params))
    ret = _recv_all(s)
    s.close()
    assert len(ret) >= 4
    msg_len = int.from_bytes(ret[:4], byteorder='little')
    assert msg_len == len(ret[4:])
    msg_body = ret[4:].decode('gbk')
    return MultiDict(urllib.parse.parse_qsl(msg_body)).to_dict()


def _pack_params(params):
    encoded_params = urllib.parse.urlencode(params).encode()
    data = len(encoded_params).to_bytes(4, byteorder='little')
    data += encoded_params
    return data


def _recv_all(s):
    chunks = []
    while True:
        chunk = s.recv(2048)
        if chunk == b'':
            break
        chunks.append(chunk)

    return b''.join(chunks)


def call_def(input_data):
    if input_data['ver'] != '1.0':
        return False, const.API_ERROR.PARAM_ERROR
    elif input_data['request_type'] == '2001':
        return True, None
    else:
        msg = {
            'bank_roll': '5432109876',
            'bank_settle_time': datetime.datetime.now()}
        return True, msg

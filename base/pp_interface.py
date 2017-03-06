#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import urllib

from werkzeug.datastructures import MultiDict

import config
from base import logger


def call2(params, host=config.PP_SERVER_HOST, port=config.PP_SERVER_PORT):
    ok, msg = call(params, host, port)
    if not ok:
        return False, msg

    logger.get("pp-interface").debug(
        'params: {}\nmsg returned: {}'.format(params, msg))

    bank_ret = msg
    if bank_ret["result"] != '0':
        if bank_ret.get("bank_time_out", '') == 'true':
            revoke(params, host, port)
            return False, "银行超时"
        return False, bank_ret["res_info"]

    return True, bank_ret


REVOKE_REQUEST_CODE_MAPPING = {
    '2005': '2101',
    '2002': '2102',
    '2009': '2103',
    '2012': '2104',

    '2007': '2105',
    '2004': '2106',
    '2011': '2107',
    '2014': '2108',

    '2015': '2109',
    '2016': '2110',
    '2017': '2111',
    '2018': '2112',
}


def revoke(params, host, port):
    logger.get("pp-interface").debug(
        'try to revoke, params: {}'.format(params)
    )
    request_type = params.get('request_type')
    revoke_request_code = REVOKE_REQUEST_CODE_MAPPING.get(request_type)
    if revoke_request_code is None:
        logger.get('pp-interface').debug(
            'revoke request code not found, do not need to revoke?')
        return

    params['request_type'] = revoke_request_code
    params['external_call'] = 1
    ok, msg = call2(params, host=host, port=port)
    if not ok:
        logger.get('pp-interface').debug('revoke fail: {}'.format(msg))
    logger.get('pp-interface').debug(
        'revoke params: {}\nmsg returned: {}'.format(params, msg))


def call(params, host=config.PP_SERVER_HOST, port=config.PP_SERVER_PORT):
    u"""与前置机通讯调用银行接口.

    @param<params>: 需要发的参数，字典形式
    @param<host>: 前置机服务主机地址
    @param<port>: 前置机服务端口

    @return: 返回值是字典形式
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((host, port))
    except:
        logger.get("pp-interface").error(
            "[connect error]: <host>=><%s>, <port>=><%s>",
            host, port, exc_info=True)
        return False, "与银行连接出错"

    s.sendall(_pack_params(params))
    ret = _recv_all(s)
    s.close()
    try:
        assert len(ret) >= 4
        msg_len = int.from_bytes(ret[:4], byteorder='little')
        assert msg_len == len(ret[4:])
        msg_body = ret[4:].decode('gbk')
    except:
        logger.get("pp-interface").error(
            "[recv data error]: <recv_data>=><%s>", ret, exc_info=True)
        return False, "银行返回数据解析出错"

    return True, MultiDict(urllib.parse.parse_qsl(msg_body)).to_dict()


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

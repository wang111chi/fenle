#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

import socket
import urllib
from werkzeug.datastructures import MultiDict

from base import constant as const
from base import logger
import config


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
        msg = {'bank_sms_time': datetime.datetime.now()}
        return True, msg
    else:
        msg = {
            'bank_roll': '5432109876',
            'bank_settle_time': datetime.datetime.now()}
        return True, msg


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

    # TODO: for testing environment which is too slow
    # to serve two successive requests!
    import time
    time.sleep(5)

    ok, msg = call2(params, host=host, port=port)
    if not ok:
        logger.get('pp-interface').debug('revoke fail: {}'.format(msg))

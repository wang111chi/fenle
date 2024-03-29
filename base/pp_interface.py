#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import urllib

from werkzeug.datastructures import MultiDict

import config
from base import logger


DEFAULT_BANK_ERROR = 1001100010  # 系统错误


def call2(params, host=config.PP_SERVER_HOST, port=config.PP_SERVER_PORT):
    ok, msg = call(params, host, port)
    if not ok:
        return False, DEFAULT_BANK_ERROR

    logger.get("pp-interface").debug(
        'params: {}\nmsg returned: {}'.format(params, msg))

    bank_ret = msg
    result = bank_ret["result"]
    if result != '0':
        maybe_revoke(bank_ret, params, host, port)
        messages = PPS_ERROR_CODES.get(result)

        logger.get("pp-interface").warn(
            "[pp error code]: pps_error_code=><{}>, "
            "internal_message=><{}>, message=><{}>, params=><{}>"
            .format(result,
                    messages[0] if messages else "未知",
                    messages[1] if messages else "未知",
                    params))

        return False, messages[2] if messages else DEFAULT_BANK_ERROR

    return True, bank_ret


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
            "[client connect error]: host=><%s>, port=><%s>, params=><%s>",
            host, port, params, exc_info=True)
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
            "[client recv data parse error]: recv_data=><%s>, params=><%s>",
            ret, params, exc_info=True)
        return False, "银行返回数据解析出错"

    return True, MultiDict(urllib.parse.parse_qsl(msg_body)).to_dict()


def maybe_revoke(bank_ret, params, host, port):
    # TODO: other conditions may be added

    if bank_ret.get("bank_time_out", '') == 'true':
        revoke(params, host, port)


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


PPS_ERROR_CODES = {
    '29910001': ('未知错误', '系统错误', 1001100010),
    '29910002': ('配置错误', '系统错误', 1001100010),
    '29910003': ('分配内存错误', '系统错误', 1001100010),
    '29910004': ('空指针', '系统错误', 1001100010),
    '29910006': ('参数错误', '参数错误', 1001100060),
    '29910021': ('打开文件失败', '系统错误', 1001100010),
    '29910022': ('未找到配置项', '系统错误', 1001100010),
    '29910023': ('XML节点为空', '系统错误', 1001100010),
    '29910024': ('XML属性为空', '系统错误', 1001100010),
    '29910025': ('XML文本为空', '系统错误', 1001100010),
    '29910026': ('正则表达式验失败', '系统错误', 1001100010),
    '29910027': ('不支持该请求类型', '系统错误', 1001100010),
    '29910090': ('Accept发送消息队列失败', '系统错误', 1001100010),
    '29910091': ('RECEIVE接收消息队列失败', '系统错误', 1001100010),
    '29910092': ('RECEIVE发送消息队列失败', '系统错误', 1001100010),
    '29910093': ('handle接收消息队列失败', '系统错误', 1001100010),
    '29910094': ('Receive处理FD不相等', '系统错误', 1001100010),
    '29910095': ('handle 线程处理FD不相等', '系统错误', 1001100010),
    '29910096': ('FD错误', '系统错误', 1001100010),
    '29920011': ('参数转换失败', '系统错误', 1001100010),
    '29920012': ('加密失败', '系统错误', 1001100010),
    '29920013': ('解密失败', '系统错误', 1001100010),
    '29920014': ('财付通内部不合法错误码', '系统错误', 1001100010),
    '29920015': ('前置不支持该请求类型', '系统错误', 1001100010),
    '29920016': ('前置不支持该IP地址访问', '系统错误', 1001100010),
    '29920017': ('前置不支持客户端协议版本号', '系统错误', 1001100010),
    '29920018': ('前置接受报文中请求参数不存在', '系统错误', 1001100010),
    '29920019': ('前置处理请求报文超时', '系统错误', 1001100010),
    '29920020': ('前置不支持该银行类型', '系统错误', 1001100010),
    '2992003': ('8583编解码类错误', '系统错误', 1001100010),
    '29920031': ('未收到数据', '系统错误', 1001100010),
    '29920032': ('未知8583消息类型', '系统错误', 1001100010),
    '29920039': ('银行协议编码失败', '系统错误', 1001100010),
    '29920040': ('银行协议解码失败', '系统错误', 1001100010),
    '29920041': ('未知消息类型', '系统错误', 1001100010),
    '29920042': ('效验消息参数失败', '系统错误', 1001100010),
    '29920043': ('建立链接失败', '系统错误', 1001100010),
    '29920044': ('接收消息失败', '系统错误', 1001100010),
    '29920045': ('接收消息失败', '系统错误', 1001100010),
    '29920046': ('访问加密机失败', '系统错误', 1001100010),
    '29920047': ('内部定义的缓存不足', '系统错误', 1001100010),
    '29920050': ('获取批次号失败', '系统错误', 1001100010),
    '29920051': ('获取billno失败', '系统错误', 1001100010),
    '29920052': ('银行返回信息不匹配', '系统错误', 1001100010),
    '29920053': ('银行返回mackey错误', '系统错误', 1001100010),
    '29920054': ('POS流水表已经存在', '系统错误', 1001100010),
    '29920055': ('银行返回消息签名错误', '系统错误', 1001100010),
    '29920056': ('单号不合法', '系统错误', 1001100010),
    '29920057': ('卡号不合法', '卡号不合法', 1001200570),
    '29920058': ('MACKEY去银行获取中', '系统错误', 1001100010),
    '29920060': ('未定义的用途编号', '系统错误', 1001100010),
    '29920061': ('POS流水表已经存在', '系统错误', 1001100010),
    '29920070': ('未匹配到请求入账记录', '系统错误', 1001100010),
    '29920071': ('银行错误对应超时错误码', '系统错误', 1001100010),
    '29920072': ('银行冲正成功，交易单需要改失败', '系统错误', 1001100010),
    '29920074': ('银行交易状态未明确', '系统错误', 1001100010),
    '29920075': ('银行返回http应答检查失败', '系统错误', 1001100010),
    '29920076': ('银行不支持此存折卡号代扣', '系统错误', 1001100010),
    '29920077': ('重复定义的错误码配置', '系统错误', 1001100010),
    '29920078': ('不支持的证件类型', '系统错误', 1001100010),
    '29920079': ('校验token失败', '系统错误', 1001100010),
    '29920080': ('流水表与请求数据不一致', '系统错误', 1001100010),
    '29920081': ('pos或银行没有冲正对应的流水记录', '系统错误', 1001100010),
    '29920082': ('已经成功不能去冲正', '系统错误', 1001100010),
    '29920083': ('还未到冲正时间', '系统错误', 1001100010),
    '29920084': ('超过冲正时间范围', '系统错误', 1001100010),
    '29920085': ('上限配置太小或超过最大批量条数', '系统错误', 1001100010),
    '299200901': ('查发卡机构', '交易失败，请联系发卡机构', 1001200901),
    '299200902': ('可电话向发卡机构查询', '交易失败，请联系发卡机构', 1001200901),
    '299200903': ('商户需要在收单系统登记', '商户未登记', 1001200903),
    '299200904': ('操作员没收卡', '没收卡，请联系收单机构', 1001200904),
    '299200905': ('发卡不予承兑', '交易失败，请联系发卡机构', 1001200901),
    '299200906': ('发卡机构故障', '交易失败，请联系发卡机构', 1001200901),
    '299200907': ('特殊条件下没收卡', '没收卡，请联系收单机构', 1001200904),
    '299200909': ('重新提交交易请求', '交易失败，请重试', 1001200909),
    '299200912': ('发卡机构不支持的交易', '交易失败，请重试', 1001200909),
    '299200913': ('金额为0 或太大', '交易金额超限，请重试', 1001200913),
    '299200914': ('卡种未在中心登记或读卡号有误', '无效卡号，请联系发卡机构', 1001200914),
    '299200915': ('此发卡机构未与中心开通业务', '此卡不能受理', 1001200915),
    '299200919': ('刷卡读取数据有误，可重新刷卡', '交易失败，请联系发卡机构', 1001200901),
    '299200920': ('无效应答', '交易失败，请联系发卡机构', 1001200901),
    '299200921': ('不做任何处理', '交易失败，请联系发卡机构', 1001200901),
    '299200922': ('第三方支付状态与中心不符，可重新签到', '操作有误，请重试', 1001200922),
    '299200923': ('不可接受的交易费', '交易失败，请联系发卡机构', 1001200901),
    '299200925': ('发卡机构未能找到有关记录', '交易失败，请联系发卡机构', 1001200901),
    '299200930': ('格式错误', '交易失败，请重试', 1001200909),
    '299200931': ('此发卡方未与中心开通业务', '此卡不能受理', 1001200915),
    '299200933': ('过期的卡，操作员可以没收', '过期卡，请联系发卡机构', 1001200933),
    '299200934': ('有作弊嫌疑的卡，操作员可以没收', '没收卡，请联系收单机构', 1001200904),
    '299200935': ('有作弊嫌疑的卡，操作员可以没收', '没收卡，请联系收单机构', 1001200904),
    '299200936': ('有作弊嫌疑的卡，操作员可以没收', '此卡有误，请换卡重试', 1001200936),
    '299200937': ('有作弊嫌疑的卡，操作员可以没收', '没收卡，请联系收单机构', 1001200904),
    '299200938': ('密码错次数超限，操作员可以没收', '密码错误次数超限', 1001200938),
    '299200939': ('可能刷卡操作有误', '交易失败，请联系发卡机构', 1001200901),
    '299200940': ('发卡行不支持的交易类型', '交易失败，请联系发卡行', 1001200940),
    '299200941': ('挂失的卡， 操作员可以没收', '没收卡，请联系收单行', 1001200941),
    '299200942': ('发卡机构找不到此账户', '交易失败，请联系发卡方', 1001200942),
    '299200943': ('被窃卡， 操作员可以没收', '没收卡，请联系收单机构', 1001200904),
    '299200944': ('可能刷卡操作有误', '交易失败，请联系发卡机构', 1001200901),
    '299200951': ('账户内余额不足', '余额不足，请查询', 1001200951),
    '299200952': ('无此支票账户', '交易失败，请联系发卡机构', 1001200901),
    '299200953': ('无此储蓄卡账户', '交易失败，请联系发卡机构', 1001200901),
    '299200954': ('过期的卡', '过期卡，请联系发卡机构', 1001200933),
    '299200955': ('密码输错', '密码错，请重试', 1001200955),
    '299200956': ('发卡机构找不到此账户', '交易失败，请联系发卡机构', 1001200901),
    '299200957': ('不允许持卡人进机构的交易', '交易失败，请联系发卡机构', 1001200901),
    '299200958': ('该商户不允许进机构的交易', '终端无效，请联系收单机构或银联', 1001200958),
    '299200959': ('有作弊嫌疑', '交易失败，请联系发卡机构', 1001200901),
    '299200960': ('受卡方与安全保密部门联系', '交易失败，请联系发卡机构', 1001200901),
    '299200961': ('超出取款金额限制', '超出取款金额限制，请联系发卡机构', 1001200961),
    '299200962': ('受限制的卡', '交易失败，请联系发卡机构', 1001200901),
    '299200963': ('违反安全保密规定', '交易失败，请联系发卡机构', 1001200901),
    '299200964': ('原始金额不正确', '交易失败，请联系发卡机构', 1001200901),
    '299200965': ('超出取款次数限制', '超出取款次数限制', 1001200965),
    '299200966': ('受卡方呼受理方安全保密部门', '交易失败，请联系收单机构或银联', 1001200966),
    '299200967': ('捕捉（没收卡）', '没收卡', 1001200967),
    '299200968': ('发卡机构规定时间内没有回答', '交易超时，请重试', 1001200968),
    '299200975': ('允许的输入PIN次数超限', '密码错误次数超限', 1001200938),
    '299200977': ('第三方支付批次与网络中心不一致', '请向网络中心签到', 1001200977),
    '299200979': ('第三方支付上传的脱机数据对账不平', '第三方支付重传脱机数据', 1001200979),
    '299200990': ('日期切换正在处理', '交易失败，请稍后重试', 1001200990),
    '299200991': ('电话查询发卡方或银联，可重作', '交易失败，请稍后重试', 1001200990),
    '299200992': ('电话查询发卡方或网络中心，可重作', '交易失败，请稍后重试', 1001200990),
    '299200993': ('交易违法、不能完成', '交易失败，请联系发卡机构', 1001200901),
    '299200994': ('查询网络中心，可重新签到作交易', '交易失败，请稍后重试', 1001200990),
    '299200995': ('调节控制错', '交易失败，请稍后重试', 1001200990),
    '299200996': ('发卡方或网络中心出现故障', '交易失败，请稍后重试', 1001200990),
    '299200997': ('终端未在中心或银机构登记', '终端未登记，请联系收单机构或银联', 1001200997),
    '299200998': ('银联收不到发卡机构应答', '交易超时，请重试', 1001200968),
    '299200999': ('可重新签到作交易', '校验错，请重新签到', 1001200999),
    '299201000': ('可重新签到作交易', '校验错，请重新签到', 1001200999),
    '299201001': ('后台出错参照63.2域内容', '没请联系收单机构（广发）', 1001201001),
    '299201002': ('未找到积分帐号', '您本卡无普通积分', 1001201002),
    '299201003': ('您当前没有积分', '您本卡无普通积分', 1001201002),
    '299201004': ('积分余额不足', '积分余额不足', 1001201004),
    '299201005': ('积分支付流水不存在', '操作有误，请重试', 1001200922),
    '299201006': ('积分支付流水已撤销', '操作有误，请重试', 1001200922),
    '299201007': ('该积分类型不可使用', '积分类型不可使用', 1001201007),
    '299201008': ('卡号不存在', '积分卡号不存在', 1001201008),
    '299201009': ('核销卡交易失败', '受限制卡', 1001201009),
    '299201010': ('虚拟卡交易失败', '受限制卡', 1001201009),
    '299201011': ('异形卡交易失败', '受限制卡', 1001201009),
    '299201012': ('附属卡交易失败', '受限制卡', 1001201009),
    '299201013': ('未设置折算率', '积分未设置折算率', 1001201013),
    '299201014': ('该卡产品在积分系统中未录入', '您本卡无普通积分', 1001201002),
    '299201015': ('积分系统拒绝注销卡进行交易', '受限制卡', 1001201009),
    '299201016': ('持卡人标志不正常', '您目前无法进行积分支付，请致电95508', 1001201016),
    '299201017': ('户口标志不正常', '您目前无法进行积分支付，请致电95508', 1001201016),
    '299201018': ('卡片标志不正常', '您目前无法进行积分支付，请致电95508', 1001201016),
    '299201019': ('积分抵扣的金额占比超过上限', '积分抵扣的金额占比超过上限', 1001201019),
    '299201020': ('积分抵扣的金额超过上限', '积分抵扣的金额超过上限', 1001201020),
    '299201021': ('积分抵扣的金额低于下限', '积分抵扣的金额低于下限', 1001201021),
    '299201022': ('积分系统其他异常', '积分系统异常', 1001201022),
    '299201023': ('验证码重复申请', '验证码重复申请', 1001201023),
    '299201024': ('验证码申请失败', '验证码申请失败', 1001201024),
    '299201025': ('验证码已使用', '验证码已使用', 1001201025),
    '299201026': ('失败', '交易失败，请联系发卡机构', 1001200901),
    '299201027': ('验证码错误', '验证码错误', 1001201027),
    '299201028': ('验证码超过有效时间', '验证码超过有效时间', 1001201028),
    '29929999': ('未知银行错误码', '系统错误', 1001100010)
}

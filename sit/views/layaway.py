#!/usr/bin/env python3

import datetime

from flask import Blueprint
from flask import request
import gevent
import requests

from base.framework import general, db_conn, form_check
from base.framework import JsonOkResponse, JsonErrorResponse, TempResponse
from base.db import engine
from base import util
from base import logic
from base import logger
from base.xform import F_str, F_int, F_mobile
from base import constant as const
from base import pp_interface as pi
from base.db import tables


layaway = Blueprint("layaway", __name__)


@layaway.route("/layaway/smscode/send", methods=["POST"])
@general("银行下发验证码")
@form_check({
    "amount": (F_int("订单交易金额")) & "strict" & "optional",
    "bankacc_no": (F_str("付款人帐号") <= 16) & "strict" & "required",
    "mobile": (F_mobile("付款人手机号码")) & "strict" & "required",
    "valid_date": F_str("有效期") & "strict" & "required",
})
def send_smscode(db, safe_vars):
    u"""
ver	int	M	4	协议版本 1.0
request_type	int	M	4	接口编号：2001
sp_id	string	M	10	商户号

sign	string	M		内部签名，案key字母排序后，再加入&signkey=xxx后算出来md5值
pay_type	int	C	4	【C】支付类型：【1 2 3】
1：信用卡分期支付
2：纯积分支付
3：积分+现金支付
bank_type	Int	M	4	银行类型值
cur_type	Int	M	4	币种
bankacc_no	string	M	32	银行账号
amount	Long	O	4	交易总金额
mobile	String	M	20	手机
client_ip	String	M	16	发起请求ip地址
sp_name	string	O	64	商户名
bank_sp_id	string	M	64	商户在银行备案的二级商户号

{'amount': '100',
 'bank_list': '20170222100101',
 'bank_type': '1001',
 'bankacc_no': '6225561640049471',
 'mobile': '18631002260',
 'request_type': '2001',
 'valid_date': '2002',
 'ver': '1.0'}
    """

    now = datetime.datetime.now()

    # 生成给银行的订单号
    bank_list = now.strftime("%Y%m%d%H%M%S")
    bank_type = const.BANK_ID.GDB

    input_data = safe_vars
    input_data.update({
        'ver': '1.0',
        'request_type': '2001',
        'bank_list': bank_list,
        'bank_type': bank_type,
    })

    ok, msg = pi.call2(input_data)
    if not ok:
        return JsonErrorResponse(msg)

    return JsonOkResponse(
        bank_list=bank_list,
        bank_sms_time=msg["bank_sms_time"],
    )


@layaway.route("/layaway/trade", methods=["POST"])
@general("分期交易")
@db_conn
@form_check({
    "amount": (F_int("订单交易金额")) & "strict" & "optional",
    "bankacc_no": (F_str("付款人帐号") <= 16) & "strict" & "required",
    "mobile": (F_mobile("付款人手机号码")) & "strict" & "required",
    "valid_date": F_str("有效期") & "strict" & "required",
    "bank_sms_time": F_str("银行下发短信时间") & "strict" & "required",
    "bank_list": F_str("给银行订单号") & "strict" & "required",
    "div_term": F_int("分期期数") & "strict" & "required",
    "uname": F_str("开户人姓名") & "strict" & "required",
    "bank_validcode": F_str("银行验证码") & "strict" & "required",
})
def trade(db, safe_vars):
    u"""
ver	int	M	4	协议版本
request_type	int	M	4	接口编号:2002
sp_id	string	M	10	商户号
sign	String	M	32	内部签名，案key字母排序后，再加入&signkey=xxx后算出来md5值
pay_type	int	C	4	【C】支付类型：【1 2 3】
1：信用卡分期支付
2：纯积分支付
3：积分+现金支付

bank_list	string	M	32	给银行订单号
list_id	String 	M	32	交易单号
bank_type	Int	M	4	银行类型值
cur_type	Int	M	4	币种
bankacc_no	string	M	32	银行账号
amount	Long	C	4	交易总金额
div_term	int	O	int	分期期数，分期支付时填入
uname	String	M	32	开户人姓名
credit_id	String	O	32	证件号码
credit_type	int	O	4	证件类型
1 身份证
mobile	String	M	20	手机
pin_code	String	O	4	信用卡pin码
bank_validcode	String	M	10	银行验证码
valid_time	String	O	4	信用卡有效时间
client_ip	String	M	16	发起请求ip地址
sp_time_stamp	Int	M	4	发起时间
sp_name	string	O	64	商户名
bank_sp_id	string	M	15	商户在银行备案的二级商户号
bank_sms_time	string	M		银行短信下发时间 yymmddhhmmss
    """
    # params = {
    #     "ver": "1.0",
    #     "request_type": "2001",
    # }

    now = datetime.datetime.now()

    # 生成订单
    db.execute(
        tables["trans_list"].insert(),
    )

    input_data = {
        'ver': '1.0',
        'request_type': '2002',
    }

    input_data.update({
        "amount": safe_vars["amount"],
        "bankacc_no": safe_vars["bankacc_no"],
        "mobile": safe_vars["mobile"],
        "valid_time": safe_vars["valid_date"],
        "bank_sms_time": safe_vars["bank_sms_time"],
        "bank_list": safe_vars["bank_list"],
        "div_term": safe_vars["div_term"],
        "bank_validcode": safe_vars["bank_validcode"],
        "uame": safe_vars["uname"],

        "bank_type": const.BANK_ID.GDB,
        "pay_type": 1,
        "cur_type": const.CUR_TYPE.RMB,
        "client_ip": request.remote_addr,
        "sp_time_stamp": now,

        "list_id": "",
        "sp_id": "",
        "bank_sp_id": "",
    })

    ok, msg = pi.call2(input_data)
    if not ok:
        return JsonErrorResponse(msg)

    return JsonOkResponse()

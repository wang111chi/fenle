#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base64 import b64decode
import urlparse
import operator
import hashlib
import urllib
from datetime import datetime

from flask import Blueprint,request
from sqlalchemy.sql import text,select
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Signature import PKCS1_v1_5 as sign_PKCS1_v1_5
from Crypto.Hash import SHA

from base.framework import db_conn
from base.framework import general
from base.framework import ApiJsonOkResponse
from base.framework import api_sign_and_encrypt_form_check, transaction
from base.xform import F_mobile, F_str, F_int
from base import constant as const
from base import logger
from base import util
from base.db import engine,meta
from base.xform import FormChecker
import config

home = Blueprint("home", __name__)


@home.route("/")
@general("首页")
# @db_conn
def index():
    return "What do you want?"


@home.route("/cardpay/apply")
@general("信用卡分期支付申请")
@api_sign_and_encrypt_form_check(engine.connect(), {
    "spid": (10 <= F_str("商户号") <= 10) & "strict" & "required",
    "sign": (F_str("签名") <= 1024) & "strict" & "required",
    "encode_type": (F_str("") <= 5) & "strict" & "required" & (
        lambda v: (v in const.ENCODE_TYPE.ALL, v)),
    "sp_userid": (F_str("用户号") <= 20) & "strict" & "required",
    "sp_tid": (F_str("支付订单号") <= 32) & "strict" & "required",
    "money": (F_int("订单交易金额")) & "strict" & "required",
    "cur_type": (F_int("币种类型")) & "strict" & "required",
    "notify_url": (F_str("后台回调地址")<=255) & "strict" & "required",
    "errpage_url": (F_str("错误页面回调地址")<=255) & "strict" & "optional",
    "memo":(F_str("订单备注")<=255) & "strict" & "required", 
    "expire_time": (F_int("订单有效时长")) & "strict" & "optional",
    "attach": (F_str("附加数据")<=255) & "strict" & "optional",
    "bankcard_type":(F_int("银行卡类型")) & "strict" & "required",
    "bank_id":(F_str("银行代号")<=4) & "strict" & "required",
    "user_type": (F_int("用户类型")) & "strict" & "required",
    "acnt_name": (F_str("付款人姓名")<=16) & "strict" & "required",
    "acnt_bankno": (F_str("付款人帐号")<=16) & "strict" & "required",
    "mobile": (F_mobile("付款人手机号码")) & "strict" & "required",
    "expiration_date": (F_str("有效期")<=11) & "strict" & "required",
    "pin_code": (F_str("cvv2")<=11) & "strict" & "required",
    "divided_term": (F_int("分期期数")) & "strict" & "required",
    "fee_duty": (F_int("手续费承担方")) & "strict" & "required",
    "channel": (F_int("渠道类型")) & "strict" & "required",
    "rist_ctrl": (F_str("风险控制数据")<=10240) & "strict" & "optional",
})
def cardpay_apply(safe_vars):
    # 处理逻辑
    abouted_field=[u'bankcard_type', u'sp_tid',u'user_type', 'acnt_bankno', u'bank_id', u'fee_duty',u'mobile',u'sp_userid', u'spid', u'cur_type', u'pin_code',u'attach',u'memo',u'acnt_name',u'divided_term',u'notify_url']

    other_field=(u'expiration_date',u'channel', u'money',u'rist_ctrl', u'expire_time',u'errpage_url', u'encode_type',u'sign',)
    
    saved_data={}
    for k in abouted_field:
        saved_data[k]=safe_vars[k]
    	
    comput_data=dict(
	list_id=33,
        bank_valicode = saved_data['pin_code'],
        valid_period='10',
        rsp_time='3',
        bank_channel='1',
        state=1,
        lstate =1,
        create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        modify_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        client_ip = '10.0.0.23',
        modify_ip = '10.0.0.23',
    )
    
    conn=engine.connect()
    fenle_bankroll_list = meta.tables['fenle_bankroll_list']
    sp_bankroll_list = meta.tables['sp_bankroll_list']
    trans_list = meta.tables['trans_list']
    
    #检查商户订单号是否已经存在
    sel = select([trans_list.c.sp_tid]).where(trans_list.c.sp_tid==safe_vars['sp_tid'])
    ret = conn.execute(sel)
    if not ret.rowcount==0:
        pass
    else:#如果不存在就生成订单
    #检查用户银行卡信息 user_bank
        sel = select([user_bank.c.sp_tid]).where(trans_list.c.sp_tid==safe_vars['sp_tid'])
        ret = conn.execute(sel)      
  
    #检查银行卡是否被冻结 user_bank
    #检查银行渠道bank_channel
    #检查合同信息
    #fee_duty  计算手续费生成金额
    ins = trans_list.insert().values(**saved_data)
    
    with transaction(conn) as trans:
        #t=conn.execute(ins,**comput_data)
        #if xxxxx:
            # if you don't want to commit, you just not call trans.finish().
         #   return error_page("xxxxxx")
        # if you want to commit, you call:
        trans.finish()
    

    ret_data = {
        "spid": "1" * 10,
        "sp_tid": "12343434",
        "encode_type": const.ENCODE_TYPE.RSA,
    }
    
    cipher_data = util.rsa_sign_and_encrypt_params(
        ret_data,
        config.FENLE_PRIVATE_KEY,
        config.TEST_MERCHANT_PUB_KEY
    )

    return ApiJsonOkResponse(
        cipher_data=cipher_data,
        clientip=request.remote_addr,
        safe_vars=safe_vars,
    )



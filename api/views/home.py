#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base64 import b64decode
import urlparse
import operator
import hashlib
import urllib
from datetime import datetime
import json

from flask import Blueprint, request
from sqlalchemy.sql import text, select, and_, or_
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Signature import PKCS1_v1_5 as sign_PKCS1_v1_5
from Crypto.Hash import SHA

from base.framework import db_conn
from base.framework import general
from base.framework import ApiJsonOkResponse
from base.framework import api_sign_and_encrypt_form_check
from base.framework import transaction
from base.framework import ApiJsonErrorResponse
from base.xform import F_mobile, F_str, F_int
from base import constant as const
from base import logger
from base import util
from base.db import engine, meta
from base.db import t_trans_list
from base.db import t_user_bank
from base.db import t_sp_bank
from base.db import t_bank_channel
from base.db import t_fenle_bankroll_list
from base.db import t_sp_bankroll_list
from base.db import t_fenle_balance
from base.db import t_sp_balance
from base.db import t_merchant_info
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
    "notify_url": (F_str("后台回调地址") <= 255) & "strict" & "required",
    "errpage_url": (F_str("错误页面回调地址") <= 255) & "strict" & "optional",
    "memo": (F_str("订单备注") <= 255) & "strict" & "required",
    "expire_time": (F_int("订单有效时长")) & "strict" & "optional",
    "attach": (F_str("附加数据") <= 255) & "strict" & "optional",
    # FIXME: review by liyuan:  user_account_type(attr)如果是枚举常量，
    # 这里应该用lambda限制常量的范围
    "user_account_type": (F_int("银行卡类型")) & "strict" & "required",
    "user_account_attr": (F_int("用户类型")) & "strict" & "required",
    "user_account_no": (F_str("付款人帐号") <= 16) & "strict" & "required",
    "user_name": (F_str("付款人姓名") <= 16) & "strict" & "optional",
    "user_mobile": (F_mobile("付款人手机号码")) & "strict" & "required",
    "bank_type": (F_str("银行代号") <= 4) & "strict" & "required",
    "expiration_date": (F_str("有效期") <= 11) & "strict" & "optional",
    "pin_code": (F_str("cvv2") <= 11) & "strict" & "optional",
    "divided_term": (F_int("分期期数")) & "strict" & "required",
    "fee_duty": (F_int("手续费承担方")) & "strict" & "required",
    # FIXME: review by liyuan:  channel如果是枚举常量，
    # 这里应该用lambda限制常量的范围
    "channel": (F_int("渠道类型")) & "strict" & "required",
    "rist_ctrl": (F_str("风险控制数据") <= 10240) & "strict" & "optional",
})
def cardpay_apply(safe_vars):
    # 处理逻辑

    # FIXME: review by liyuan:  conn统一用db_conn装饰器获取
    conn = engine.connect()
    # 从mysql检查商户spid是否存在
    s = select([t_merchant_info.c.status,
                t_merchant_info.c.mer_key,
                t_merchant_info.c.rsa_pub_key]).where(
        t_merchant_info.c.spid == safe_vars['spid'])
    merchant_ret = conn.execute(s).first()
    if merchant_ret is None:
        return ApiJsonErrorResponse(const.API_ERROR.SPID_NOT_EXIST)
    elif merchant_ret['status'] == const.MERCHANT_STATUS.CLOSURED:  # 判断是否被封禁
        # FIXME: review by liyuan:  CLOSURED命名不妥？没有这个单词
        return ApiJsonErrorResponse(const.API_ERROR.MERCHANT_CLOSURED)
    merchant_pubkey = merchant_ret['rsa_pub_key']

    # 预备返回的参数
    ret_data = dict(
        spid=safe_vars['spid'],
        sp_tid=safe_vars['sp_tid'],
        money=safe_vars['money'],
        cur_type=safe_vars['cur_type'],
        divided_term=safe_vars['divided_term'],
        fee_duty=safe_vars['fee_duty'],
        pay_type=const.PRODUCT_TYPE.FENQI,
        user_account_type=safe_vars['user_account_type'],
        encode_type=safe_vars['encode_type'], )

    # 检查商户订单号是否已经存在
    sel = select([t_trans_list.c.status, t_trans_list.c.list_id]).where(and_(
        t_trans_list.c.spid == safe_vars['spid'],
        t_trans_list.c.sp_tid == safe_vars['sp_tid']))
    list_ret = conn.execute(sel).first()
    if list_ret is not None:   # 如果已经存在
        ret_data.update({
            "list_id": list_ret['list_id'],
            "result": list_ret['status'], })
        cipher_data = util.rsa_sign_and_encrypt_params(
            ret_data,
            config.FENLE_PRIVATE_KEY,
            merchant_pubkey)
        return ApiJsonOkResponse(
            cipher_data=cipher_data,
            safe_vars=safe_vars,)

    # 请求参数中的不需要计算的字段
    solid_field = set((
        u'spid', u'sp_userid', u'sp_tid', u'cur_type',
        u'notify_url', u'memo', u'attach', u'user_account_no',
        u'user_account_type', u'user_account_attr',
        u'user_name', u'user_mobile', u'bank_type',
        u'divided_term', u'pin_code', u'fee_duty', u'channel'))
    solid_field = solid_field & set(safe_vars.keys())
    ''' other_field = (u'expiration_date', u'money', u'rist_ctrl',
    u'expire_time', u'errpage_url', u'encode_type', u'sign',)'''

    saved_data = dict()
    for k in solid_field:
        saved_data[k] = safe_vars[k]

    comput_data = dict(
        rsp_time='3',
        # FIXME: review by liyuan:  pay_type和product_type怎么都用的PRODUCT_TYPE？
        pay_type=const.PRODUCT_TYPE.FENQI,
        product_type=const.PRODUCT_TYPE.FENQI,)

    # 检查银行渠道是否可用，是否验证手机号
    sel = select([t_bank_channel.c.is_enable,
                  t_bank_channel.c.fenqi_fee_percent,
                  t_bank_channel.c.bank_valitype,
                  t_bank_channel.c.bank_channel,
                  t_bank_channel.c.singlepay_vmask]).where(
        t_bank_channel.c.bank_type == safe_vars['bank_type'])
    channel_ret = conn.execute(sel).first()
    if channel_ret is None:
        return ApiJsonErrorResponse(const.API_ERROR.BANK_NOT_EXIST)

    if channel_ret['is_enable'] == const.BOOLEAN.FALSE:  # 银行渠道不可用
        return ApiJsonErrorResponse(const.API_ERROR.BANK_CHANNEL_UNABLE)

    if channel_ret['singlepay_vmask'] is not None:
        # 验证有效期
        # FIXME: review by liyuan:  这里不能用 not in来检查，optional的字段
        # 依然会在safe_vars中，只是为None而已，下面的几个检查存在一样的问题
        if (channel_ret['singlepay_vmask'] & const.PAY_MASK.EXPIRATION) and \
           ('expiration_date' not in safe_vars):
            return ApiJsonErrorResponse(const.API_ERROR.NO_EXPIRATION_DATE)

        # 验证安全码
        if (channel_ret['singlepay_vmask'] & const.PAY_MASK.PIN_CODE) and \
           ('pin_code' not in safe_vars):
            return ApiJsonErrorResponse(const.API_ERROR.NO_PIN_CODE)

        # 验证姓名
        if (channel_ret['singlepay_vmask'] & const.PAY_MASK.NAME) and \
           ('user_name' not in safe_vars):
            return ApiJsonErrorResponse(const.API_ERROR.NO_USER_NAME)

    if channel_ret['bank_valitype'] == const.BANK_VALITYPE.MOBILE_VALID:
        # 需要验证手机号
        is_need_mobile = True
    else:
        is_need_mobile = False
    bank_fee_percent = json.loads(channel_ret['fenqi_fee_percent'])
    if str(safe_vars['divided_term']) not in bank_fee_percent:
        # FIXME @review by liyuan: Not_EXIST 笔误?
        return ApiJsonErrorResponse(const.API_ERROR.DIVIDED_TERM_NOt_EXIST)
    comput_data.update({
        'bank_channel': channel_ret['bank_channel'],
        'bank_fee': bank_fee_percent[str(safe_vars['divided_term'])] *
        safe_vars['money'] / 10000})

    # 检查用户银行卡信息 user_bank
    now = datetime.now()
    sel = select([t_user_bank.c.lstate]).where(
        t_user_bank.c.account_no == safe_vars['user_account_no'])
    user_bank_ret = conn.execute(sel).first()
    if user_bank_ret is None:
        user_bank_info = dict(
            account_no=safe_vars['user_account_no'],
            # FIXME: review by liyuan:  account_type和account_attr怎么一样？
            account_type=safe_vars['user_account_type'],
            account_attr=safe_vars['user_account_type'],
            user_name=safe_vars['user_name'],
            bank_type=safe_vars['bank_type'],
            bank_sname='',
            bank_branch='',
            mobile=safe_vars['user_mobile'],
            # FIXME: review by liyuan:  这里的state和lstate用了magic number
            state=1,
            lstate=1,
            create_time=now,
            modify_time=now)
        conn.execute(t_user_bank.insert(), user_bank_info)
    else:
        # 检查银行卡是否被冻结 user_bank
        if user_bank_ret['lstate'] == const.LSTATE.HUNG:  # 冻结标志
            return ApiJsonErrorResponse(const.API_ERROR.BANKCARD_FREEZED)

    # 检查合同信息

    # 查 sp_bank 的 fenqi_fee_percent
    sel = select([t_sp_bank.c.fenqi_fee_percent,
                  t_sp_bank.c.bank_spid,
                  t_sp_bank.c.divided_term]).where(and_(
                      t_sp_bank.c.spid == safe_vars['spid'],
                      t_sp_bank.c.bank_type == safe_vars['bank_type']))
    sp_bank_ret = conn.execute(sel).first()
    if sp_bank_ret is None:
        return ApiJsonErrorResponse(const.API_ERROR.NO_SP_BANK)

    # FIXME review by liyuan: 不要这样用，用 not in
    if not str(safe_vars['divided_term']) in \
            sp_bank_ret['divided_term'].split(','):
        # FIXME reviwe by liyuan: 笔误
        return ApiJsonErrorResponse(const.API_ERROR.DIVIDED_TERM_NOt_EXIST)

    fenqi_fee_percent = json.loads(sp_bank_ret['fenqi_fee_percent'])
    if str(safe_vars['divided_term']) not in fenqi_fee_percent:
        # FIXME reviwe by liyuan: 笔误
        return ApiJsonErrorResponse(const.API_ERROR.DIVIDED_TERM_NOt_EXIST)
    fee_percent = fenqi_fee_percent[str(safe_vars['divided_term'])]
    comput_data.update({'fee': safe_vars['money'] * fee_percent / 10000})
    bank_spid = sp_bank_ret['bank_spid']

    # 生成订单相关数据
    comput_data.update(dict(
        list_id=util.gen_trans_list_id(
            safe_vars['spid'],
            safe_vars['bank_type']),
        bank_tid=util.gen_bank_tid(bank_spid),
        # FIXME: review by liyuan: backid应该是银行返回时才有的数据，这里还没有，返回后再update
        bank_backid='321',  # 暂时拟的
        status=const.STATUS.PAYING,  # 支付中
        lstate=const.LSTATE.VALID,  # 有效的
        create_time=now,
        modify_time=now))

    # FIXME: review by liyuan: saved_data在一开始就定义，在这里才用？上下文隔得太远，
    # 完全可以放到这里再赋值
    ins_trans_list = t_trans_list.insert().values(**saved_data)

    # fee_duty  计算手续费生成金额
    if safe_vars['fee_duty'] == const.FEE_DUTY.BUSINESS:  # 商户付手续费
        comput_data.update({
            'amount': safe_vars['money'],
            'pay_num': safe_vars['money'], })
    else:
        pass
        # TODO 用户付手续费情形

    if is_need_mobile:
        comput_data.update({'status': const.STATUS.MOBILE_CHECKING})
        # FIXME: review by liyuan: 这里的语义很奇怪，上面已经存了saved_data，这里的意思是要
        # 再更新comput_data？这样用确定没有问题？即使没有问题也不建议这样写，把要存的数据在一个
        # 地方赋值不是更明确？要么在这里统一插，要么在insert().values里面统一插
        conn.execute(ins_trans_list, comput_data)
        # TODO 调用银行下发验证码，根据结果更新 bank_backid
        ret_data.update({
            "list_id": comput_data['list_id'],
            "result": comput_data['status'], })
        cipher_data = util.rsa_sign_and_encrypt_params(
            ret_data,
            config.FENLE_PRIVATE_KEY,
            # FIXME: review by liyuan: merchant_pubkey在很早定义了，这里才用，上下文了隔得太远
            merchant_pubkey)
        return ApiJsonOkResponse(
            list_id=comput_data['list_id'],
            cipher_data=cipher_data,
            safe_vars=safe_vars)
    else:
        sp_bankroll_data = dict(
            list_id=comput_data['list_id'],
            spid=safe_vars['spid'],
            bankroll_type=const.SP_BANKROLL_TYPE.IN,
            status=const.STATUS.MOBILE_CHECKING,  # 支付中
            user_name=safe_vars['user_name'],
            cur_type=safe_vars['cur_type'],
            bank_type=safe_vars['bank_type'],
            create_time=comput_data['create_time'],
            modify_time=comput_data['modify_time'],
            product_type=const.PRODUCT_TYPE.FENQI,
            list_sign=const.LIST_SIGN.WELL)

        fenle_bankroll_data = dict(
            list_id=comput_data['list_id'],
            spid=safe_vars['spid'],
            fenle_account_id=config.FENLE_ACCOUNT_NO,
            fenle_account_type=const.FENLE_ACCOUNT.VIRTUAL,  # 1真实，2虚拟
            status=const.STATUS.MOBILE_CHECKING,  # 支付中
            bank_type=safe_vars['bank_type'],
            cur_type=safe_vars['cur_type'],
            user_name=safe_vars['user_name'],
            create_time=comput_data['create_time'],
            modify_time=comput_data['modify_time'],
            product_type=const.PRODUCT_TYPE.FENQI, )

        # fee_duty  计算手续费生成金额
        if safe_vars['fee_duty'] == const.FEE_DUTY.BUSINESS:  # 商户付手续费
            # FIXME: review by liyuan: 格式混乱
            sp_bankroll_data.update({
                'pay_num': comput_data['pay_num'], 'sp_num':
                comput_data['pay_num'] - comput_data['fee']})
            fenle_bankroll_data.update({
                'pay_num': comput_data['pay_num'],
                'fact_amount':
                comput_data['pay_num'] - comput_data['bank_fee'],
                'income_num': comput_data['fee'] - comput_data['bank_fee']})
        else:
            pass
            # TODO 用户付手续费情形

        with transaction(conn) as trans:
            conn.execute(ins_trans_list, comput_data)
            fenle_bankroll_data.update({
                'bank_tid': comput_data['bank_tid'],
                'bank_backid': comput_data['bank_backid']})
            ret = conn.execute(t_sp_bankroll_list.insert(), sp_bankroll_data)
            last_id = ret._saved_cursor._last_insert_id
            conn.execute(t_fenle_bankroll_list.insert(), fenle_bankroll_data)
            trans.finish()

        # TODO 调用银行支付请求接口,更新余额
        # FIXME: review by liyuan: 下面这些修改要更新修改时间
        udp_fenle_bankroll = t_fenle_bankroll_list.update().where(and_(
            t_fenle_bankroll_list.c.bank_tid == comput_data['bank_tid'],
            t_fenle_bankroll_list.c.bank_type == safe_vars['bank_type']))\
            .values(status=const.STATUS.PAY_SUCCESS)

        udp_fenle_balance = t_fenle_balance.update().where(and_(
            t_fenle_balance.c.account_no == config.FENLE_ACCOUNT_NO,
            t_fenle_balance.c.bank_type == config.FENLE_BANK_TYPE)).values(
            balance=t_fenle_balance.c.balance +
                comput_data['fee'] - comput_data['bank_fee'])

        udp_sp_bankroll = t_sp_bankroll_list.update().where(
            t_sp_bankroll_list.c.id == last_id).values(
            status=const.STATUS.PAY_SUCCESS)

        # FIXME: review by liyuan: 商家余额可能还不存在(第一次)，这时需要插入新的，
        # 可以用insert on duplidate update语法
        udp_sp_balance = t_sp_balance.update().where(and_(
            t_sp_balance.c.spid == safe_vars['spid'],
            t_sp_balance.c.cur_type == safe_vars['cur_type'])).values(
            balance=t_sp_balance.c.balance +
                comput_data['pay_num'] - comput_data['fee'])

        udp_trans_list = t_trans_list.update().where(
            t_trans_list.c.list_id == comput_data['list_id']).values(
            status=const.STATUS.PAY_SUCCESS)

        with transaction(conn) as trans:
            conn.execute(udp_fenle_bankroll)
            conn.execute(udp_fenle_balance)
            conn.execute(udp_sp_bankroll)
            conn.execute(udp_sp_balance)
            conn.execute(udp_trans_list)
            trans.finish()

        # FIXME: review by liyuan: 同样是上下文隔得太远，一是难以阅读，
        # 二是定义得太早浪费性能，因为有可能提前返回了
        ret_data.update({
            "list_id": comput_data['list_id'],
            "result": const.STATUS.PAY_SUCCESS, })
        cipher_data = util.rsa_sign_and_encrypt_params(
            ret_data,
            config.FENLE_PRIVATE_KEY,
            merchant_pubkey)
        return ApiJsonOkResponse(
            list_id=comput_data['list_id'],
            cipher_data=cipher_data,
            safe_vars=safe_vars, )


@home.route("/cardpay/confirm")
@general("信用卡分期支付确认")
@api_sign_and_encrypt_form_check(engine.connect(), {
    "spid": (10 <= F_str("商户号") <= 10) & "strict" & "required",
    "sign": (F_str("签名") <= 1024) & "strict" & "required",
    "encode_type": (F_str("") <= 5) & "strict" & "required" & (
        lambda v: (v in const.ENCODE_TYPE.ALL, v)),
    "list_id": (F_str("支付订单号") <= 32) & "strict" & "required",
    "user_mobile": (F_mobile("付款人手机号码")) & "strict" & "required",
    "bank_valicode": (F_str("银行下发的验证码") <= 32) & "strict" & "required",
})
def cardpay_confirm(safe_vars):
    # FIXME: review by liyuan:  conn统一用db_conn装饰器获取
    conn = engine.connect()

    # 检查订单状态
    sel = select([t_trans_list.c.status,
                  t_trans_list.c.user_mobile,
                  t_trans_list.c.user_account_no,
                  t_trans_list.c.bank_type,
                  t_trans_list.c.spid,
                  t_trans_list.c.cur_type,
                  t_trans_list.c.paynum,
                  t_trans_list.c.fee,
                  t_trans_list.c.bank_tid,
                  t_trans_list.c.bank_backid,
                  t_trans_list.c.bank_fee]).where(
        t_trans_list.c.list_id == safe_vars['list_id'])
    list_ret = conn.execute(sel).first()
    if list_ret is None:
        return ApiJsonErrorResponse(const.API_ERROR.LIST_ID_NOT_EXIST)

    if list_ret['status'] != const.STATUS.MOBILE_CHECKING:
        return ApiJsonErrorResponse(const.API_ERROR.CONFIRM_STATUS_ERROR)

    # FIXME: review by liyuan:  这里逻辑错误?
    if list_ret['user_mobile'] == const.STATUS.MOBILE_CHECKING:
        return ApiJsonErrorResponse(const.API_ERROR.CONFIRM_MOBILE_ERROR)

    # TODO 用验证码调用银行接口
    now = datetime.now()
    sp_bankroll_data = dict(
        list_id=safe_vars['list_id'],
        spid=list_ret['spid'],
        bankroll_type=const.SP_BANKROLL_TYPE.IN,
        status=const.STATUS.MOBILE_CHECKING,  # 支付中
        cur_type=list_ret['cur_type'],
        bank_type=list_ret['bank_type'],
        create_time=now,
        modify_time=now,
        product_type=const.PRODUCT_TYPE.FENQI,
        list_sign=const.LIST_SIGN.WELL)

    fenle_bankroll_data = dict(
        list_id=safe_vars['list_id'],
        spid=list_ret['spid'],
        fenle_account_id=config.FENLE_ACCOUNT_NO,
        fenle_account_type=const.FENLE_ACCOUNT.VIRTUAL,  # 1真实，2虚拟
        status=const.STATUS.MOBILE_CHECKING,  # 支付中
        bank_type=list_ret['bank_type'],
        cur_type=list_ret['cur_type'],
        bank_tid=list_ret['bank_tid'],
        bank_backid=list_ret['bank_backid'],
        create_time=now,
        modify_time=now,
        product_type=const.PRODUCT_TYPE.FENQI, )

    # 根据银行返回信息更新余额及流水
    udp_sp_balance = t_sp_balance.update().where(and_(
        t_sp_balance.c.spid == list_ret['spid'],
        t_sp_balance.c.cur_type == list_ret['cur_type'])).values(
        balance=t_sp_balance.c.balance +
            list_ret['paynum'] - list_ret['fee'])

    udp_fenle_balance = t_fenle_balance.update().where(and_(
        t_fenle_balance.c.account_no == config.FENLE_ACCOUNT_NO,
        t_fenle_balance.c.bank_type == config.FENLE_BANK_TYPE)).values(
        balance=t_fenle_balance.c.balance +
            list_ret['fee'] - list_ret['bank_fee'])

    udp_trans_list = t_trans_list.update().where(
        t_trans_list.c.list_id == safe_vars['list_id']).values(
        status=const.STATUS.PAY_SUCCESS)

    # FIXME: review by liyuan:  这里的逻辑有问题，在发请求前先开一个事务插入两个流水，
    # 同时更新trans_list的状态，然后向银行发请求，请求返回后才是再开一个事务更新各流水和余额
    with transaction(conn) as trans:
        conn.execute(t_sp_bankroll_list.insert(), sp_bankroll_data)
        conn.execute(t_fenle_bankroll_list.insert(), fenle_bankroll_data)

        conn.execute(udp_sp_balance)
        conn.execute(udp_fenle_balance)
        conn.execute(udp_trans_list)
        trans.finish()

    # FIXME: review by liyuan:  返回的数据为空？应该是跟第一步中的不需要验证码时的情况一致
    return ApiJsonOkResponse({})

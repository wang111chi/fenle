#!/usr/bin/env python
# -*- coding: utf-8 -*-


class BOOLEAN(object):
    FALSE = 0
    TRUE = 1

    ALL = (FALSE, TRUE)


class REQUEST_STATUS(object):
    SUCCESS = 0                        # 请求成功
    FAIL = 1                           # 请求失败


class API_ERROR(object):
    PARAM_ERROR = 207001
    MERCHANT_NOT_EXIST = 207200
    SPID_NOT_EXIST = 207201
    DECRYPT_ERROR = 207266
    SIGN_INVALID = 207267
    
    BANKCARD_NOT_EXIST = 207300
    BANKCARD_FREEZED = 207301
    BANK_CHANNEL_UNABLE  = 207310    

    NAMES = {
        PARAM_ERROR: u"参数格式错误",
        MERCHANT_NOT_EXIST: u"商户不存在",
        SPID_NOT_EXIST: u"mysql中不存在此商户号",
        DECRYPT_ERROR: u"解密失败",

        SIGN_INVALID: u"校验签名失败",
        BANKCARD_NOT_EXIST : u"银行卡未注册",
        BANKCARD_FREEZED : u"银行卡冻结",
        BANK_CHANNEL_UNABLE : u"银行渠道不可用"
    }


class ENCODE_TYPE(object):

    u"""签名类型."""

    MD5 = "MD5"
    RSA = "RSA"

    ALL = (MD5, RSA)


class HTTP_METHOD(object):

    u"""HTTP 请求方法."""

    GET = 0
    POST = 1
    ALL = (GET, POST)


class CALLBACK_URL(object):

    u"""URL回调相关常量."""

    class MODE(object):
        CARDPAY_APPLY_SUCCESS_NOTIFY = 1    # 分期支付API请求成功回调

        ALL = (
            CARDPAY_APPLY_SUCCESS_NOTIFY,
        )

    class STATUS(object):
        INIT = 0     # 待处理(还未回调过)
        PENDING = 1  # 待重试(需要下一次重试)
        DONE = 2     # 回调成功(不再需要重试)
        FAIL = 3     # 回调失败(重试次数已达到，同样不再需要重试)
  

class CUR_TYPE(object):
    RMB = 1
	

class CARD_TYPE(object):
    u"""银行卡类型"""
    
    QUASI_CREDIT_CARD=1
    DEBIT_CARD=2
    CREDIT_CARD=3

    NAMES={
        QUASI_CREDIT_CARD:u"贷记卡",
        DEBIT_CARD:u"借记卡",
        CREDIT_CARD:u"信用卡"    
    }

    
class USER_TYPE(object):
    u"""用户类型"""
    
    PERSONAL=1    
    ENTERPRISE=2
    
    NAMES={
        PERSONAL:u"个人",
        ENTERPRISE:u"企业"    
    }	


class FEE_DUTY(object):
    CUSTOM=1
    BUSINESS=2

    NAMES={
        CUSTOM:u"用户",
        BUSINESS:u"商户"
    
}

#!/usr/bin/env python
# -*- coding: utf-8 -*-


class BOOLEAN(object):
    FALSE = 0
    TRUE = 1

    ALL = (FALSE, TRUE)


class BANK_ID(object):
    GDB = 1001
    ICBC = 1002
    ABC = 1003
    BOC = 1004
    CMBC = 1005
    CMB = 1006
    BCM = 1007
    CEB = 1008
    CIB = 1009 
    
    NAMES = {
        GDB: u"GuangDong Development Bank广发银行",
        ICBC: u"Industrial and Commercial Bank工商银行",
        ABC: u"Agricultural Bank农业银行",
        BOC: u"Bank Of China中国银行",
        CMBC: u"中国民生银行",
        CMB: u"China Merchant Bank招商银行",
        BCM: u"Bank of Communications交通银行",
        CEB: u"China Everbright Bank光大银行",
        CIB: u"Industrial Bank兴业银行"
    } 

class REQUEST_STATUS(object):
    SUCCESS = 0                        # 请求成功
    FAIL = 1                           # 请求失败


class API_ERROR(object):
    PARAM_ERROR = 207001

    SPID_NOT_EXIST = 207200
    MERCHANT_CLOSURED = 207201    

    DECRYPT_ERROR = 207366
    SIGN_INVALID = 207367
    
    BANKCARD_NOT_EXIST = 207300
    BANKCARD_FREEZED = 207301
    BANK_NOT_EXIST = 207310
    BANK_CHANNEL_UNABLE  = 207311   
     
    NAMES = {
        PARAM_ERROR : u"参数格式错误",
        
        SPID_NOT_EXIST : u"分乐不存在此商户号",
        MERCHANT_CLOSURED : u"商户被封禁了",         

        DECRYPT_ERROR : u"解密失败",
        SIGN_INVALID : u"校验签名失败",
        
        BANKCARD_NOT_EXIST : u"银行卡未注册",
        BANKCARD_FREEZED : u"银行卡冻结",
        BANK_NOT_EXIST : u"分乐暂不支持该银行",
        BANK_CHANNEL_UNABLE : u"银行渠道不可用",
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
    RMB = 1  #人民币
	

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

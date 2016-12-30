#!/usr/bin/env python
# -*- coding: utf-8 -*-


class BOOLEAN(object):
    FALSE = 0
    TRUE = 1

    ALL = (FALSE, TRUE)


class PRODUCT_TYPE(object):
    FENQI = 1  # 分期
    JIFEN = 2  # 积分


class SETTLE_TYPE(object):
    DAY_SETTLE = 1     # 日结
    MONTH_SETTLE = 2   # 月结


class REQUEST_STATUS(object):
    SUCCESS = 0                        # 请求成功
    FAIL = 1                           # 请求失败
    AUTH_ERROR = 2                     # 授权失败/未登录


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


class CUR_TYPE(object):
    RMB = 0     # 人民币
    DOLLAR = 1  # 美元

    ALL = (RMB, DOLLAR)


class LSTATE(object):
    VALID = 1  # 有效
    HUNG = 2  # 挂起
    INVALID = 3  # 作废


class BANKROLL_TYPE(object):
    IN = 1
    OUT = 2
    FREEZE = 3
    DEFREEZE = 4


class STATUS(object):
    PAY_SUCCESS = 1
    PAY_FALSE = 2
    PAYING = 4
    MOBILE_CHECKING = 3


class MERCHANT_STATUS(object):
    CLOSURED = 1  # 封禁
    OPEN = 0  # 开放


class LIST_SIGN:
    u"""流水标记"""

    WELL = 0  # 正常
    RUSHED = 1  # 被冲正
    RUSHING = 2  # 冲正


class BANK_VALITYPE(object):
    MOBILE_VALID = 0x0001


class PAY_MASK(object):
    u"""验证单笔接口参数掩码"""

    ACCOUNT = 0x00000001
    NAME = 0x00000002
    IDCARD = 0x00000004
    MOBILE = 0x00000008
    PIN_CODE = 0x00000010
    EXPIRATION = 0x00000020
    IDCARD_NAME = 0x00000040

    NAMES = {
        ACCOUNT: u"验证银行账户有效性",
        NAME: u"验证银行账户与姓名一致性",
        IDCARD: u"验证银行账户与证件一致性",
        MOBILE: u"验证银行账户与预留手机号一致性",
        PIN_CODE: u"验证银行账户与安全码一致性",
        EXPIRATION: u"验证银行账户与有效期一致性",
        IDCARD_NAME: u"验证证件与姓名的一致性"}


class ACCOUNT_TYPE(object):

    u"""银行卡类型."""

    CREDIT_CARD = 0
    DEBIT_CARD = 1

    NAMES = {
        DEBIT_CARD: u"借记卡",
        CREDIT_CARD: u"信用卡"
    }


class ACCOUNT_ATTR(object):

    u"""用户类型."""

    PERSONAL = 1
    ENTERPRISE = 2

    NAMES = {
        PERSONAL: u"个人",
        ENTERPRISE: u"企业",
    }


class FENLE_ACCOUNT(object):
    VIRTUAL = 3  # 虚拟第三方户
    ACTUAL = 4   # 真实用户


class FEE_DUTY(object):
    BUSINESS = 1
    CUSTOM = 2

    NAMES = {
        BUSINESS: u"商户",
        CUSTOM: u"用户",
    }


class API_ERROR(object):
    PARAM_ERROR = 207001

    SPID_NOT_EXIST = 207200
    MERCHANT_CLOSURED = 207201

    DECRYPT_ERROR = 207366
    SIGN_INVALID = 207367

    ACCOUNT_NOT_EXIST = 207300
    ACCOUNT_FREEZED = 207301
    BANK_NOT_EXIST = 207310
    BANK_CHANNEL_UNABLE = 207311

    MOBILE_NO_VALIDATA = 207400
    NO_EXPIRATION_DATE = 207401
    NO_PIN_CODE = 207402
    NO_USER_NAME = 207403

    NO_SP_BANK = 207504
    DIVIDED_TERM_NOT_EXIST = 207505

    NAMES = {
        PARAM_ERROR: u"参数格式错误",
        SPID_NOT_EXIST: u"分乐不存在此商户号",
        MERCHANT_CLOSURED: u"商户被封禁了",
        DECRYPT_ERROR: u"解密失败",
        SIGN_INVALID: u"校验签名失败",
        ACCOUNT_NOT_EXIST: u"银行卡未注册",
        ACCOUNT_FREEZED: u"银行卡冻结",
        BANK_NOT_EXIST: u"分乐暂不支持该银行",
        BANK_CHANNEL_UNABLE: u"银行渠道不可用",
        MOBILE_NO_VALIDATA: u"手机号验证码不存在",
        NO_EXPIRATION_DATE: u"有效期需要验证",
        NO_PIN_CODE: u"安全码需要验证",
        NO_USER_NAME: u"用户姓名需要验证",
        NO_SP_BANK: u"商家银行没有相关服务",
        DIVIDED_TERM_NOT_EXIST: u"不存在这样的分期期数服务"}


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


class SESSION(object):
    KEY_WX_PROG_SESSION_KEY = "wx_prog_session_key"
    KEY_WX_PROG_OPENID = "wx_prog_openid"

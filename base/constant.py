#!/usr/bin/env python
# -*- coding: utf-8 -*-


class BOOLEAN(object):
    FALSE = 0
    TRUE = 1

    ALL = (FALSE, TRUE)


class CHANNEL(object):

    API = 1
    SP_SYSTEM = 2  # 商户系统

    ALL = (API, SP_SYSTEM, )


class SETTLE_TYPE(object):
    DAY_SETTLE = 1     # 日结
    MONTH_SETTLE = 2   # 月结


class REQUEST_STATUS(object):
    SUCCESS = 0  # 请求成功
    FAIL = 1     # 请求失败


class PRODUCT(object):
    LAYAWAY = 1       # 分期
    POINT = 2         # 积分
    POINT_CASH = 3    # 积分+现金
    CONSUME = 4       # 普通信用卡消费
    TRADE_REQUEST_TYPE = {
        LAYAWAY: '2002',
        POINT: '2009',
        POINT_CASH: '2012',
        CONSUME: '2005',
    }
    CANCEL_REQUEST_TYPE = {
        LAYAWAY: '2004',
        POINT: '2011',
        POINT_CASH: '2014',
        CONSUME: '2007',
    }
    REFUND_REQUEST_TYPE = {
        LAYAWAY: '2003',
        POINT: '2010',
        POINT_CASH: '2013',
        CONSUME: '2006',
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


class CUR_TYPE(object):
    RMB = 0     # 人民币
    DOLLAR = 1  # 美元

    ALL = (RMB, DOLLAR)


class BIZ(object):

    u"""业务类型"""

    TRANS = 1  # 交易
    REFUND = 2  # 退款
    SETTLE = 3  # 结算
    WITHDRAW = 4  # 提现
    DEPOSIT = 5  # 充值

    # C2B = 4  # 反结算
    # FREEZE = 7  # 冻结
    # DEFREEZE = 8  # 解冻
    # ARREARS_IN = 9  # 欠款入
    # ARREARS_OUT = 10  # 欠款出


class USER_BANK_STATUS(object):
    INIT = 0  # 初始化
    CERTIFIED = 1  # 经认证了的
    FREEZING = 2  # 用户被冻结
    LOG_OFF = 3  # 注销


class TRANS_STATUS(object):
    PAYING = 0  # 支付中
    PAY_SUCCESS = 1  # 支付成功
    PAY_FALSE = 2  # 支付失败


class REFUND_STATUS(object):
    REFUNDING = 0  # 退款中
    REFUND_SUCCESS = 1  # 退款成功
    REFND_FALSE = 2  # 退款失败


class REFUND_STATUS(object):
    REFUNDING = 0  # 退款中
    REFUND_SUCCESS = 1  # 退款成功
    REFND_FALSE = 2  # 退款失败


class MERCHANT_STATUS(object):
    FORBID = 1  # 封禁
    OPEN = 0  # 开放


class BANK_VALITYPE(object):
    MOBILE_VALID = 0x0001
    MOBILE_NOT_VALID = 0x0002


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


class ACCOUNT_CLASS(object):
    B = 1
    C = 2
    ARREARS = 3


class ACCOUNT_TYPE(object):

    u"""银行卡类型."""

    CREDIT_CARD = 0
    DEBIT_CARD = 1

    ALL = (CREDIT_CARD, DEBIT_CARD)

    NAMES = {
        DEBIT_CARD: u"借记卡",
        CREDIT_CARD: u"信用卡"
    }


class ACCOUNT_ATTR(object):

    u"""用户类型."""

    PERSONAL = 1
    ENTERPRISE = 2

    ALL = (PERSONAL, ENTERPRISE)

    NAMES = {
        PERSONAL: u"个人",
        ENTERPRISE: u"企业",
    }


class FENLE_ACCOUNT(object):
    ACTUAL = 1  # 真实用户
    VIRTUAL = 2  # 虚拟第三方户


class FEE_DUTY(object):
    BUSINESS = 1
    CUSTOM = 2

    ALL = (BUSINESS, CUSTOM)
    NAMES = {
        BUSINESS: u"商户",
        CUSTOM: u"用户",
    }


class API_ERROR(object):
    PARAM_ERROR = 207001

    SPID_NOT_EXIST = 207200
    MERCHANT_FORBID = 207201

    REPEAT_PAY = 207202

    ACCOUNT_NOT_EXIST = 207300
    ACCOUNT_FREEZED = 207301
    BANK_NOT_EXIST = 207310
    BANK_CHANNEL_UNABLE = 207311

    DECRYPT_ERROR = 207366
    SIGN_INVALID = 207367

    MOBILE_NO_VALIDATA = 207400
    NO_EXPIRATION_DATE = 207401
    NO_PIN_CODE = 207402
    NO_USER_NAME = 207403

    NO_SP_BANK = 207504
    PRODUCT_NOT_EXIST = 207514
    DIVIDED_TERM_NOT_EXIST = 207505
    SP_BALANCE_NOT_EXIST = 207506
    FENLE_BALANCE_NOT_EXIST = 207507

    LIST_ID_NOT_EXIST = 207600
    CONFIRM_STATUS_ERROR = 207601
    CONFIRM_MOBILE_ERROR = 207602
    CONFIRM_SPTID_ERROR = 207603
    CONFIRM_ACCOUNT_NO_ERROR = 207604
    LIST_STATUS_ERROR = 207605

    NO_USER_PAY = 207701
    INSERT_ERROR = 207702
    REPEAT_SETTLE = 207703

    REFUND_LESS_BALANCE = 207801

    NAMES = {
        PARAM_ERROR: u"参数格式错误",
        SPID_NOT_EXIST: u"分乐不存在此商户号",
        MERCHANT_FORBID: u"商户被封禁了",
        DECRYPT_ERROR: u"解密失败",
        SIGN_INVALID: u"校验签名失败",
        ACCOUNT_NOT_EXIST: u"银行卡未注册",
        REPEAT_PAY: u"订单已经存在了，请别重复提交",
        ACCOUNT_FREEZED: u"银行卡冻结",
        BANK_NOT_EXIST: u"分乐暂不支持该银行",
        BANK_CHANNEL_UNABLE: u"银行渠道不可用",
        MOBILE_NO_VALIDATA: u"手机号验证码不存在",
        NO_EXPIRATION_DATE: u"有效期需要验证",
        NO_PIN_CODE: u"安全码需要验证",
        NO_USER_NAME: u"用户姓名需要验证",
        PRODUCT_NOT_EXIST: u"服务产品不存在",
        NO_SP_BANK: u"商家银行没有相关服务",
        DIVIDED_TERM_NOT_EXIST: u"不存在这样的分期期数服务",
        SP_BALANCE_NOT_EXIST: u"商户余额账户不存在",
        FENLE_BALANCE_NOT_EXIST: u"分乐余额账户不存在",
        LIST_STATUS_ERROR: u"订单状态错误",
        NO_USER_PAY: u"不支持用户付手续费情形",
        INSERT_ERROR: u"数据库插入异常",
        REFUND_LESS_BALANCE: u"余额不足退款"}


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
        GDB: u"GuangDong Development Bank",
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

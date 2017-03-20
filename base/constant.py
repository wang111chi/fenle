#!/usr/bin/env python
# -*- coding: utf-8 -*-


class BOOLEAN(object):
    FALSE = 0
    TRUE = 1

    ALL = (FALSE, TRUE)


class CHANNEL(object):

    API = 1
    SP_SYSTEM = 2  # 商户系统

    ALL = (API, SP_SYSTEM)


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

    ALL = (RMB,)


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
    PAY_FAIL = 2  # 支付失败


class REFUND_STATUS(object):
    REFUNDING = 0  # 退款中
    REFUND_SUCCESS = 1  # 退款成功
    REFUND_FAIL = 2  # 退款失败
    CHECKING = 3


class MERCHANT_STATUS(object):
    FORBID = 1  # 封禁
    OPEN = 0  # 开放


class BANK_VALITYPE(object):
    MOBILE_VALID = 0
    MOBILE_NOT_VALID = 1


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

    ALL = (CREDIT_CARD, )

    NAMES = {
        CREDIT_CARD: u"信用卡",
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
    SP = 1
    USER = 2

    ALL = (SP, USER)
    NAMES = {
        SP: u"商户",
        USER: u"用户",
    }


class API_ERROR(object):

    """API错误常量

共10位

10 01xx xxxx 银行错误

10 00xx xxxx 业务错误
     ||
    模块号

模块号：

00: 业务系统错误
如：
10 0000 0001 业务系统错误(500，程序出错)
10 0000 0002 输入参数错误

01: 用户身份相关
02: 商户身份相关
03: 分乐身份相关

10: 正向交易通用
11: 分期交易
12: 积分交易
13: 积分+现金
14: 现金
15: 预授权
16: 预授权确认

31: 退款
32: 提现
    """

    # TODO 按上述格式适配业务错误代码

    PARAM_ERROR = 207001
    DECRYPT_ERROR = 207066
    SIGN_INVALID = 207067

    REPEAT_PAY_MOBILE_ERROR = 207211
    REPEAT_PAY_ACCOUNTNO_ERROR = 207212
    REPEAT_PAY_AMOUNT_ERROR = 207213
    REPEAT_PAY_BANKTYPE_ERROR = 207215

    SPID_NOT_EXIST = 207200
    MERCHANT_FORBID = 207201

    ACCOUNT_NOT_EXIST = 207300
    ACCOUNT_FREEZED = 207301
    ACCOUNT_TYPE_ERROR = 207302
    CUR_TYPE_ERROR = 207303
    BANK_NOT_EXIST = 207310
    BANK_CHANNEL_UNABLE = 207311

    MOBILE_NO_VALIDATA = 207400
    NO_EXPIRATION_DATE = 207401
    NO_PIN_CODE = 207402
    NO_USER_NAME = 207403

    NO_SP_BANK = 207504
    PRODUCT_NOT_EXIST = 207514
    DIV_TERM_NOT_EXIST = 207505
    SP_BALANCE_NOT_EXIST = 207506
    FENLE_BALANCE_NOT_EXIST = 207507

    LIST_ID_NOT_EXIST = 207600
    LIST_STATUS_ERROR = 207605

    NO_USER_PAY = 207701
    INSERT_ERROR = 207702
    REPEAT_SETTLE = 207703
    BANK_ERROR = 207710

    REFUND_LESS_BALANCE = 207801
    REFUND_TIME_OVER = 207802

    NAMES = {
        PARAM_ERROR: u"参数格式错误",
        SPID_NOT_EXIST: u"分乐不存在此商户号",
        MERCHANT_FORBID: u"商户被封禁了",
        DECRYPT_ERROR: u"解密失败",
        SIGN_INVALID: u"校验签名失败",
        ACCOUNT_NOT_EXIST: u"银行卡未注册",
        REPEAT_PAY_MOBILE_ERROR: u"重复提交手机号错误",
        REPEAT_PAY_ACCOUNTNO_ERROR: u"重复提交银行卡号错误",
        REPEAT_PAY_AMOUNT_ERROR: u"重复提交金额错误",
        REPEAT_PAY_BANKTYPE_ERROR: u"重复提交银行类别错误",
        ACCOUNT_FREEZED: u"银行卡冻结",
        BANK_NOT_EXIST: u"分乐暂不支持该银行",
        ACCOUNT_TYPE_ERROR: u"分乐暂不支持此银行卡类型",
        CUR_TYPE_ERROR: u"分乐暂不支持此币种类型",
        BANK_CHANNEL_UNABLE: u"银行渠道不可用",
        MOBILE_NO_VALIDATA: u"手机号验证码不存在",
        NO_EXPIRATION_DATE: u"有效期需要验证",
        NO_PIN_CODE: u"安全码需要验证",
        NO_USER_NAME: u"用户姓名需要验证",
        PRODUCT_NOT_EXIST: u"服务产品不存在",
        NO_SP_BANK: u"商家银行没有相关服务",
        DIV_TERM_NOT_EXIST: u"不存在这样的分期期数服务",
        SP_BALANCE_NOT_EXIST: u"商户余额账户不存在",
        FENLE_BALANCE_NOT_EXIST: u"分乐余额账户不存在",
        LIST_STATUS_ERROR: u"订单状态错误",
        LIST_ID_NOT_EXIST: u"订单不存在",
        NO_USER_PAY: u"不支持用户付手续费情形",
        INSERT_ERROR: u"数据库插入异常",
        BANK_ERROR: u"银行错误",
        REFUND_LESS_BALANCE: u"余额不足退款",
        REFUND_TIME_OVER: u"退款时间已过期"}

    BANK_ERRORS = {
        1001100010: '系统错误',
        1001100060: '参数错误',
        1001200570: '卡号不合法',
        1001200901: '交易失败，请联系发卡机构',
        1001200903: '商户未登记',
        1001200904: '没收卡，请联系收单机构',
        1001200909: '交易失败，请重试',
        1001200913: '交易金额超限，请重试',
        1001200914: '无效卡号，请联系发卡机构',
        1001200915: '此卡不能受理',
        1001200922: '操作有误，请重试',
        1001200933: '过期卡，请联系发卡机构',
        1001200936: '此卡有误，请换卡重试',
        1001200938: '密码错误次数超限',
        1001200940: '交易失败，请联系发卡行',
        1001200941: '没收卡，请联系收单行',
        1001200942: '交易失败，请联系发卡方',
        1001200951: '余额不足，请查询',
        1001200955: '密码错，请重试',
        1001200958: '终端无效，请联系收单机构或银联',
        1001200961: '超出取款金额限制，请联系发卡机构',
        1001200965: '超出取款次数限制',
        1001200966: '交易失败，请联系收单机构或银联',
        1001200967: '没收卡',
        1001200968: '交易超时，请重试',
        1001200977: '请向网络中心签到',
        1001200979: '第三方支付重传脱机数据',
        1001200990: '交易失败，请稍后重试',
        1001200997: '终端未登记，请联系收单机构或银联',
        1001200999: '校验错，请重新签到',
        1001201001: '没请联系收单机构（广发）',
        1001201002: '您本卡无普通积分',
        1001201004: '积分余额不足',
        1001201007: '积分类型不可使用',
        1001201008: '积分卡号不存在',
        1001201009: '受限制卡',
        1001201013: '积分未设置折算率',
        1001201016: '您目前无法进行积分支付，请致电95508',
        1001201019: '积分抵扣的金额占比超过上限',
        1001201020: '积分抵扣的金额超过上限',
        1001201021: '积分抵扣的金额低于下限',
        1001201022: '积分系统异常',
        1001201023: '验证码重复申请',
        1001201024: '验证码申请失败',
        1001201025: '验证码已使用',
        1001201027: '验证码错误',
        1001201028: '验证码超过有效时间',
    }

    NAMES.update(BANK_ERRORS)


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

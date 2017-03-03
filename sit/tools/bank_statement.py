#!/usr/bin/env python3

import importme

import datetime
import os

import click
from sqlalchemy import select, text

import config
from base import constant as const
from base.db import engine, tables


"""

消息类型	字符型	MTI -- 0200/0210等	4	每个接口消息类型不同，但是固定
主账号/卡号	字符型	域2- Primary Account Number	19	用户卡号
交易处理码	字符型	域3- Processing Code	6	固定的交易码
交易金额	字符型	域4- Amount Of Transactions	12	金额
受卡方系统跟踪号	字符型	域11- System Trace Audit Number	6	6位的给请求序列号
要求：在某个商户的某个时间点上不能重复
受卡方所在地时间	字符型	域12- Time Of Local Transaction	6	这个时间是由银行返回的，在请求下发短信时返回，主要是用于结算
受卡方所在地日期	字符型	域13- Date Of Local Transaction	4	同上
服务点条件码	字符型	域25- Point Of Service Condition Mode	2	填：
64	分期付款
65	积分消费
检索参考号	字符型	域37- Retrieval Reference Number	12	银行返回的订单号
授权标识应答码	字符型	域38- Authorization Identification Response	6	积分加现金交换广发的卡核心会返回授权码（汇聚这边需要保存这个字段，在对账的时候传入）
应答码	字符型	域39-应答码(Response Code)	2	银行返回的响应码
受卡机终端标识码	字符型	域41- Card Acceptor Terminal Identification	8	 无卡交易时，无真实终端，可以构造一个虚拟终端编号，尽可能区分商户交易能的编号。
受卡方标识码	字符型	域42- Card Acceptor Identification Code	15	15位子商户号
商户名称	字符型	域43- Card Acceptor Identification Code	40	商户名
原始商户编号	字符型	域48- Additional Data - Private	15	域48的前15位
可忽略，不填
附加金额	字符型	域54- Balance Amount	20	积分+现金消费时，表示积分所抵扣的金额
原交易匹配域	字符型	域61- Original Message	32	由12，11，13，三个域拼接（注意顺序）
交易方式	字符型	域22-服务点输入方式码,即持卡人数据（如PAN和PIN）的输入方式。服务点（Point Of Service）是指各种交易始发场合。	4	0-无卡交易
1-有卡交易
默认填1
分期期数	字符型		2	分期交易时填写，其他填空
预留字段1	字符型		40	未用
预留字段2	字符型		60	未用
预留字段3	字符型		80	未用
预留字段4	字符型		128	未用
预留字段5	字符型		128	未用

""" # noqa


FIELDS_LENGTH = (4, 19, 6, 12, 6, 6, 4, 2, 12, 6, 2, 8, 15,
                 40, 15, 20, 32, 4, 2, 40, 60, 80, 128, 128)

CODES = {
    const.PRODUCT_TYPE.CONSUME: (
        ("0200", "000000", "08"),
        ("0200", "200000", "08"),
        ("0220", "200000", "08"),
    ),

    const.PRODUCT_TYPE.LAYAWAY: (
        ("0200", "000000", "79"),
        ("0200", "200000", "79"),
        ("0220", "200000", "79"),
    ),

    const.PRODUCT_TYPE.POINT: (
        ("0200", "000000", "65"),
        ("0200", "200000", "65"),
        ("0220", "200000", "65"),
    ),

    const.PRODUCT_TYPE.POINT_CASH: (
        ("0200", "000000", "66"),
        ("0200", "200000", "66"),
        ("0220", "200000", "66"),
    ),

    const.PRODUCT_TYPE.PREAUTH: (
        ("0100", "030000", "18"),
        ("0100", "200000", "18"),
        ("", "", ""),
    ),

    const.PRODUCT_TYPE.PREAUTH_DONE: (
        ("0200", "000000", "18"),
        ("0200", "200000", "18"),
        ("", "", ""),
    ),
}


def validate_date(ctx, param, value):
    if value is None:
        return datetime.date.today() + datetime.timedelta(-1)

    try:
        present_date = datetime.datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise click.BadParameter('date needs to be in format 0000-00-00')

    return present_date.date()


@click.command()
@click.option('--date',
              callback=validate_date,
              help='The date(xxxx-xx-xx) for statement.')
def cli(date):
    main(date,
         (const.PRODUCT_TYPE.CONSUME,
          const.PRODUCT_TYPE.LAYAWAY,
          const.PRODUCT_TYPE.PREAUTH_DONE,),
         "wuka")

    main(date,
         (const.PRODUCT_TYPE.POINT,
          const.PRODUCT_TYPE.POINT_CASH,),
         "jifen")


def main(present_date, products, trade):
    db = engine.connect()
    present_date = datetime.date(2017, 3, 3)

    bank_settle_time_b = present_date.strftime("%m%d")
    bank_settle_time_e = (present_date +
                          datetime.timedelta(1)).strftime("%m%d")

    # 正向交易单
    t_trans_list = tables["trans_list"]
    result = db.execute(
        t_trans_list.select()
        .where(t_trans_list.c.status.in_([
            const.TRANS_STATUS.OK,
            const.TRANS_STATUS.CANCEL,
            const.TRANS_STATUS.REFUND,
        ]))
        .where(t_trans_list.c.product.in_(products))
        .where(t_trans_list.c.bank_settle_time < bank_settle_time_e)
        .where(t_trans_list.c.bank_settle_time >= bank_settle_time_b)
    )

    trans_list = [dict(row) for row in result]

    # 退款单
    t_refund_list = tables["refund_list"]
    s = select([
        text("trans_list.*, refund_list.bank_list as refund_bank_list, "
             "refund_list.bank_settle_time as refund_bank_settle_time, "
             "refund_list.bank_roll as refund_bank_roll, "
             "refund_list.mode as refund_mode")
    ]).select_from(
        t_refund_list.join(
            t_trans_list,
            t_refund_list.c.trans_id == t_trans_list.c.id)
    ).where(
        t_refund_list.c.status == const.REFUND.STATUS.OK
    ).where(
        t_refund_list.c.product.in_(products)
    ).where(
        t_refund_list.c.bank_settle_time < bank_settle_time_e
    ).where(
        t_refund_list.c.bank_settle_time >= bank_settle_time_b
    )

    result = db.execute(s)
    refund_list = [dict(row) for row in result]

    dir_ = os.path.realpath(__file__)
    dir_ = os.path.split(dir_)[0]

    filename = "{}/files/{}_{}.txt".format(
        dir_, trade, present_date.strftime("%Y%m%d"))
    with open(filename, mode="wb") as f:
        for trans in trans_list + refund_list:
            fields = handle_trans(trans)
            assert len(fields) == 24
            fields = map(str, fields)
            fields = map(lambda x: x.encode("gbk"), fields)
            fields = map(lambda fl: (
                fl[0] + b" " * max(0, fl[1] - len(fl[0])))[:fl[1]],
                zip(fields, FIELDS_LENGTH))
            f.write(b"".join(fields) + b"\r\n")


def handle_trans(trans):
    stmt = []

    product = trans["product"]
    refund_mode = trans.get("refund_mode", None)

    code_index = 0
    if refund_mode == const.REFUND.MODE.CANCEL:
        code_index = 1
    elif refund_mode == const.REFUND.MODE.REFUND:
        code_index = 2
    codes = CODES[product][code_index]

    # 消息类型
    stmt.append(codes[0])

    # 主账号/卡号
    stmt.append(trans["bankacc_no"])

    # 交易处理码
    stmt.append(codes[1])

    # 交易金额
    stmt.append(trans["amount"])

    # 受卡方系统跟踪号
    bank_list = trans["bank_list"] if refund_mode \
        is None else trans["refund_bank_list"]
    stmt.append(bank_list[-6:])

    # 受卡方所在地时间
    # 受卡方所在地日期
    bank_settle_time = trans["bank_settle_time"] if refund_mode \
        is None else trans["refund_bank_settle_time"]
    stmt.append(bank_settle_time[-6:])
    stmt.append(bank_settle_time[:4])

    # 服务点条件码
    stmt.append(codes[2])

    # 检索参考号
    bank_roll = trans["bank_roll"] if refund_mode \
        is None else trans["refund_bank_roll"]
    stmt.append(bank_roll)

    # 授权标识应答码
    # TODO
    stmt.append("")

    # 应答码
    stmt.append("00")

    # 受卡机终端标识码
    stmt.append(trans["terminal_id"])

    # 受卡方标识码
    stmt.append(trans["bank_spid"])

    # 商户名称
    stmt.append("")

    # 原始商户编号
    stmt.append("")

    # 附加金额
    stmt.append(trans["jf_deduct_money"] if
                product == const.PRODUCT_TYPE.POINT_CASH else "")

    # 原交易匹配域
    match_field = ""
    if refund_mode is not None:
        match_field = trans["bank_settle_time"][-6:] + \
            trans["bank_list"][-6:] + \
            trans["bank_settle_time"][:4]
    stmt.append(match_field)

    # 交易方式
    stmt.append("0")

    # 分期期数
    stmt.append(trans["div_term"] if
                product == const.PRODUCT_TYPE.LAYAWAY else "")

    # 预留字段1
    stmt.append("")
    # 预留字段2
    stmt.append("")
    # 预留字段3
    stmt.append("")
    # 预留字段4
    stmt.append("")
    # 预留字段5
    stmt.append("")

    return stmt


if __name__ == "__main__":
    cli()

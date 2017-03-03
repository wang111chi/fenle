#!/usr/bin/env python3

import importme

import datetime

import config
from base import constant as const
from base.db import engine, tables

PRODUCT = const.PRODUCT_TYPE.POINT

db = engine.connect()


def main():
    present_date = datetime.date(2017, 3, 2)
    bank_settle_time_b = present_date.strftime("%m%d")
    bank_settle_time_e = (present_date +
                          datetime.timedelta(1)).strftime("%m%d")

    print(bank_settle_time_b)
    print(bank_settle_time_e)

    # 正向交易单
    t_trans_list = tables["trans_list"]
    result = db.execute(
        t_trans_list.select()
        .where(t_trans_list.c.status.in_([
            const.TRANS_STATUS.OK,
            const.TRANS_STATUS.CANCEL,
            const.TRANS_STATUS.REFUND,
        ]))
        .where(t_trans_list.c.product == const.PRODUCT_TYPE.POINT)
        .where(t_trans_list.c.bank_settle_time < bank_settle_time_e)
        .where(t_trans_list.c.bank_settle_time >= bank_settle_time_b)
    )

    trans_list = [dict(row) for row in result]

    print(trans_list)

    # 退款单
    # t_refund_list = tables["refund_list"]


if __name__ == "__main__":
    main()

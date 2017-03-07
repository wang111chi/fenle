#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.sql import select
from sqlalchemy import and_

from base.framework import ApiJsonErrorResponse
from base.framework import update_sp_balance
from base.framework import transaction
from base import constant as const
from base.db import t_trans_list
from base.db import t_fenle_balance
from base.db import t_fenle_history
from base.db import t_sp_history
import config


def settle(db):
    """
    1、只有支付成功的交易单才会结算；

    2、已经结算成功的不会重复被结算；

    3、当天退款成功的不会再结算
    """

    sel = select([
        t_trans_list.c.list_id,
        t_trans_list.c.spid,
        t_trans_list.c.status,
        t_trans_list.c.paynum,
        t_trans_list.c.fee,
        t_trans_list.c.bank_fee,
        t_trans_list.c.divided_term,
        t_trans_list.c.fee_duty,
        t_trans_list.c.bank_type]).where(and_(
            t_trans_list.c.status == const.TRANS_STATUS.PAY_SUCCESS,
            t_trans_list.c.settle_time is None,
            t_trans_list.c.refund_id is None))

    list_ret = db.execute(sel)
    if list_ret.first() is None:
        return False, const.API_ERROR.LIST_ID_NOT_EXIST

    now = datetime.datetime.now()
    sp_history_data = {
        'biz': const.BIZ.SETTLE,
        'create_time': now}

    for alist in list_ret:
        sp_history_data = {
            'ref_str_id': alist['list_id']}

        sp_history_data.update({
            'amount': alist['paynum'],
            'spid': alist['spid'],
            'account_class': const.ACCOUNT_CLASS.B})

        udp_sp_balance_b = update_sp_balance(
            alist['spid'], const.ACCOUNT_CLASS.B,
            alist['paynum'], now)

        udp_sp_balance_c = update_sp_balance(
            alist['spid'], const.ACCOUNT_CLASS.C,
            alist['paynum'] - alist['fee'], now)

        udp_spfen_balance = update_sp_balance(
            config.FENLE_SPID, const.ACCOUNT_CLASS.C,
            alist['fee'] - alist['bank_fee'], now)

        with transaction(db) as trans:
            db.execute(t_sp_history.insert(), sp_history_data)
            db.execute(udp_sp_balance_b)

            sp_history_data.update({
                'amount': alist['paynum'] - alist['fee'],
                'account_class': const.ACCOUNT_CLASS.C})
            db.execute(t_sp_history.insert(), sp_history_data)
            db.execute(udp_sp_balance_c)

            sp_history_data.update({
                'amount': alist['fee'] - alist['bank_fee'],
                'spid': config.FENLE_SPID})
            db.execute(t_sp_history.insert(), sp_history_data)
            db.execute(udp_spfen_balance)

            trans.finish()

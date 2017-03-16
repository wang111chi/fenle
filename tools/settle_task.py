#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.sql import select
from sqlalchemy import and_

import importme
from task import Task, TaskIdent, RunType
from base.db import t_trans_list
from base import dblogic as dbl
from base import const


class SettleTask(Task):

    u"""结算任务."""

    IDENT = TaskIdent.TEST

    def _run(self):
        sel = select([
            t_trans_list.c.id,
            t_trans_list.c.spid,
            t_trans_list.c.amount,
            t_trans_list.c.fee,
            t_trans_list.c.bank_fee,
            t_trans_list.c.product,
            t_trans_list.c.create_time,
            t_trans_list.c.bank_type]).where(and_(
                t_trans_list.c.status == const.TRANS_STATUS.PAY_SUCCESS,
                t_trans_list.c.refund_id is None,
                t_trans_list.c.settle_time is None))
        list_ret = self.db.execute(sel)
        if list_ret.first() is None:
            return False, const.API_ERROR.LIST_ID_NOT_EXIST

        now = datetime.datetime.now()
        for a_list in list_ret:
            dbl.settle_a_list(self.db, a_list, now)

        print("settle task runned")
        self.run_success = True


if __name__ == "__main__":
    SettleTask(RunType.MANUAL).run()

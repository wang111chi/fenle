#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy import MetaData
from redis import StrictRedis

import config


# ############ mysql ################

meta = MetaData()

engine = create_engine(config.DATABASE_URL)
meta.reflect(bind=engine)
engine = engine.execution_options(autocommit=True)

t_trans_list = meta.tables['trans_list']
t_merchant_info = meta.tables['merchant_info']
t_user_bank = meta.tables['user_bank']
t_sp_bank = meta.tables['sp_bank']
t_bank_channel = meta.tables['bank_channel']
t_sp_history = meta.tables['sp_balance_history']
t_fenle_history = meta.tables['fenle_balance_history']
t_sp_balance = meta.tables['sp_balance']
t_fenle_balance = meta.tables['fenle_balance']
t_callback_url = meta.tables['callback_url']
t_task_log = meta.tables['task_log']
t_task_footprint = meta.tables['task_footprint']
t_refund_list = meta.tables['refund_list']
t_settle_list = meta.tables['settle_list']


# ########## redis #################

def _redis_wrapper():
    redis_cli = [None]

    def _get_redis():
        if redis_cli[0] is None:
            redis_cli[0] = StrictRedis(**config.REDIS)
        return redis_cli[0]

    return _get_redis


get_redis = _redis_wrapper()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy import MetaData
import config

meta = MetaData()

engine = create_engine(config.DATABASE_URL)
meta.reflect(bind=engine)
engine = engine.execution_options(autocommit=True)

t_trans_list = meta.tables['trans_list']
t_merchant_info = meta.tables['merchant_info']
t_user_bank = meta.tables['user_bank']
t_sp_bank = meta.tables['sp_bank']
t_bank_channel = meta.tables['bank_channel']
t_fenle_bankroll_list = meta.tables['fenle_bankroll_list']
t_sp_bankroll_list = meta.tables['sp_bankroll_list']
t_sp_balance = meta.tables['sp_balance']
t_fenle_balance = meta.tables['fenle_balance']
t_callback_url = meta.tables['callback_url']

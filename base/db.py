#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy import MetaData

meta = MetaData()
engine = create_engine('postgresql+pg8000://postgres:123456@postgres/jidui')
meta.reflect(bind=engine)

t_merchant_info = meta.tables['merchant_info']

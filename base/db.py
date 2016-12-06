#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy import MetaData
import config

meta = MetaData()

engine = create_engine(config.DATABASE_URL)
meta.reflect(bind=engine)
engine = engine.execution_options(autocommit=True)

t_merchant_info = meta.tables['merchant_info']

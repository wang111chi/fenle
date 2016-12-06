#!/usr/bin/env python
# -*- coding: utf-8 -*-

# remember to import me at first!
import importme

from base.framework import transaction
from base.db import engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.sql import select


def test_transaction():
    metadata = MetaData()
    metadata.bind = engine
    t_users = Table('test_users', metadata,
                       Column('id', Integer, primary_key=True),
                       Column('name', String),
                       Column('fullname', String),
    )

    t_users.create(engine, checkfirst=True)

    db = engine.connect()
    db.execute(t_users.delete())

    with transaction(db) as trans:
        ins = t_users.insert().values(name='jack', fullname='Jack Jones')
        db.execute(ins)

    s = select([t_users]).where(t_users.c.name == 'jack')
    result = db.execute(s)
    assert result.fetchone() is None

    with transaction(db) as trans:
        ins = t_users.insert().values(name='jack', fullname='Jack Jones')
        db.execute(ins)
        trans.finish()

    result = db.execute(
        t_users.select().where(t_users.c.name == 'jack'))

    assert result.fetchone() is not None
    t_users.drop(engine)

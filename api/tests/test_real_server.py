from gevent import monkey
monkey.patch_all()

import datetime

import gevent
import requests
import pytest
import sqlalchemy
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey

import wsgi_handler
from base.db import engine, meta
from base.framework import transaction


API_PREFIX = "http://server:3031"


def test_server_work():
    """服务器可以访问."""
    r = requests.get(API_PREFIX + "/test")
    assert r.status_code == 200


def test_concurrent_access():
    """服务器可以并发访问."""
    def req():
        return requests.get(API_PREFIX + "/test")

    jobs = [gevent.spawn(req) for i in range(100)]
    gevent.joinall(jobs)
    assert all(job.value.status_code == 200 for job in jobs)


def test_gevent_work():
    """gevent起作用."""
    def req():
        return requests.get(API_PREFIX + "/test/slow")

    start = datetime.datetime.now()

    jobs = [gevent.spawn(req) for i in range(100)]
    gevent.joinall(jobs)

    end = datetime.datetime.now()

    assert (end - start).days == 0
    assert (end - start).seconds < 10
    assert all(job.value.status_code == 200 for job in jobs)


def test_mysql_not_blocking():
    """MySQL不会阻塞."""
    def req():
        return requests.get(API_PREFIX + "/test/mysql/slow")

    start = datetime.datetime.now()

    jobs = [gevent.spawn(req) for i in range(10)]
    gevent.joinall(jobs)

    end = datetime.datetime.now()

    assert (end - start).days == 0
    assert (end - start).seconds < 18
    assert all(job.value.status_code == 200 for job in jobs)


def test_concurrent_update_without_lock(db, t_balance):
    """并发修改时不加锁的后果."""
    db.execute(t_balance.insert(), id=1, balance=10)

    def req():
        """如果余额足，则扣除相应余额."""
        _db = engine.connect()

        # 这里未加锁，导致出现race condition
        r = _db.execute("select * from test_balance where id=1")
        balance = r.first()
        if balance["balance"] >= 10:
            _do_something()
            _db.execute(
                "update test_balance set balance=balance-10 where id=1")

    jobs = [gevent.spawn(req) for i in range(2)]
    gevent.joinall(jobs)

    # 余额减了两次，变成了负数
    assert db.execute(
        "select * from test_balance where id=1").first()["balance"] < 0


def test_concurrent_update_with_lock(db, t_balance):
    """并发修改的正确方式."""
    db.execute(t_balance.insert(), id=1, balance=10)

    def req():
        _db = engine.connect()

        # 开启事务
        with transaction(_db) as trans:
            # 加排他锁
            r = _db.execute(
                "select * from test_balance where id=1 for update")
            balance = r.first()
            if balance["balance"] >= 10:
                _do_something()
                _db.execute(
                    "update test_balance set balance=balance-10 where id=1")
            trans.finish()

    jobs = [gevent.spawn(req) for i in range(2)]
    gevent.joinall(jobs)

    assert db.execute(
        "select * from test_balance where id=1").first()["balance"] >= 0


def test_concurrent_insert_error(db, t_balance):
    """并发插入的问题."""
    def req():
        _db = engine.connect()

        # 先查询
        r = _db.execute("select * from test_balance where id=1")
        if r.first() is None:
            _do_something()
            # 如果没查到则插入，这里存在race condition，两个线程可能同时都查不到，
            # 然后导致重复插入，或者抛unique key重复异常(有unique key的情况下)
            _db.execute(t_balance.insert(), id=1, balance=0)
        else:
            return "exist"

        return "ok"

    jobs = [gevent.spawn(req) for i in range(2)]
    gevent.joinall(jobs)

    # 产生重复插入异常()
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        for job in jobs:
            job.get()


def test_concurrent_insert_ok(db, t_balance):
    """并发插入的正确方式."""
    def req():
        _db = engine.connect()

        # 直接插入，处理异常(确保有unique key的情况下)
        try:
            _db.execute(t_balance.insert(), id=1, balance=0)
        except sqlalchemy.exc.IntegrityError:
            return "exist"

        return "ok"

    jobs = [gevent.spawn(req) for i in range(2)]
    gevent.joinall(jobs)

    assert set(job.value for job in jobs) == {"ok", "exist"}


def test_str_lock(db):
    from base.framework import lock_str

    def req():
        _db = engine.connect()

        with lock_str(_db, "test") as locked:
            if not locked:
                return "error"
            _do_something(3)
            return "ok"

    jobs = [gevent.spawn(req) for i in range(10)]
    gevent.joinall(jobs)

    assert set(job.value for job in jobs) == {"ok", "error"}
    assert db.execute("SELECT IS_FREE_LOCK(%s)", "test").first()[0] == 1


def _do_something(duration=2):
    import time
    time.sleep(duration)


@pytest.fixture()
def db():
    conn = engine.connect()
    # clear all tables
    for table in reversed(meta.sorted_tables):
        conn.execute(table.delete())

    return conn


@pytest.fixture(scope='function')
def t_balance():
    metadata = MetaData()
    metadata.bind = engine
    t_balance = Table(
        'test_balance', metadata,
        Column('id', Integer, primary_key=True, autoincrement=False),
        Column('balance', Integer, nullable=False, server_default='0'))

    t_balance.create(checkfirst=True)
    yield t_balance
    t_balance.drop()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import importme

import datetime

import gevent
from gevent.pool import Pool

import config as cfg
from base import logger
from base.db import engine
from base import logic
from base.db import engine
from base.db import t_callback_url
from base import constant as const

def main():
    db = engine.connect()

    while True:
        stmt = t_callback_url.select(
            t_callback_url.c.status == const.CALLBACK_URL.STATUS.PENDING
        )
        result = db.execute(stmt)

        p = Pool(10)
        p.map(retry_callback, result)
        gevent.sleep(1)


def retry_callback(callback_url):
    callback_id = callback_url["id"]
    mode = callback_url["mode"]
    retry_times = callback_url["retry_times"]
    call_time = callback_url["call_time"]
    url = callback_url["url"]
    method = callback_url["method"]
    body = callback_url["body"]

    retry_config = cfg.CALLBACK_URL[mode]
    retry_interval = retry_config[retry_times]

    now = datetime.datetime.now()
    if call_time + datetime.timedelta(seconds=retry_interval) > now:
        return

    is_success, resp_code, resp_body = logic.callback_url(
        callback_id, mode, url, method=method, body=body,
        logger=logger.get("tools-log"))

    if is_success:
        status = const.CALLBACK_URL.STATUS.DONE
    else:
        retry_times += 1
        if retry_times < len(retry_config):
            status = const.CALLBACK_URL.STATUS.PENDING
        else:
            status = const.CALLBACK_URL.STATUS.FAIL

    db = engine.connect()

    stmt = t_callback_url.update().where(
        t_callback_url.c.id == callback_id
    ).values(
        resp_code=resp_code,
        resp_body=resp_body,
        call_time=now,
        retry_times=retry_times,
        is_call_success=const.BOOLEAN.TRUE if \
        is_success else const.BOOLEAN.FALSE,
        status=status
    )

    db.execute(stmt)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# remember to import me at first!

from . import importme

import gevent
import time


def win():
    return 'You win!'


def fail():
    raise Exception('You fail at failing.')


def test_spawn():
    winner = gevent.spawn(win)
    loser = gevent.spawn(fail)

    print(winner.started)  # True
    print(loser.started)   # True

    # Exceptions raised in the Greenlet, stay inside the Greenlet.
    try:
        gevent.joinall([winner, loser])
    except Exception:
        print('This will never be reached')

    print(winner.value)  # 'You win!'
    print(loser.value)   # None

    print(winner.ready())  # True
    print(loser.ready())   # True

    print(winner.successful())  # True
    print(loser.successful())   # False

    # The exception raised in fail, will not propagate outside the
    # greenlet. A stack trace will be printed to stdout but it
    # will not unwind the stack of the parent.

    print(loser.exception)

    assert True


def echo(i):
    time.sleep(0.001)
    return i


from gevent.pool import Pool


def test_pool():
    p = Pool(5)
    run1 = [a for a in p.imap_unordered(echo, range(10))]
    run2 = [a for a in p.imap_unordered(echo, range(10))]
    run3 = [a for a in p.imap_unordered(echo, range(10))]
    run4 = [a for a in p.imap_unordered(echo, range(10))]

    assert(run1 == run2 == run3 == run4)

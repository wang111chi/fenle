#!/usr/bin/env python
# -*- coding: utf-8 -*-

# remember to import me at first!

import importme

import gevent

def win():
    return 'You win!'

def fail():
    raise Exception('You fail at failing.')

def test_spawn():
    winner = gevent.spawn(win)
    loser = gevent.spawn(fail)

    print(winner.started) # True
    print(loser.started)  # True

    # Exceptions raised in the Greenlet, stay inside the Greenlet.
    try:
        gevent.joinall([winner, loser])
    except Exception as e:
        print('This will never be reached')

    print(winner.value) # 'You win!'
    print(loser.value)  # None

    print(winner.ready()) # True
    print(loser.ready())  # True

    print(winner.successful()) # True
    print(loser.successful())  # False

    # The exception raised in fail, will not propagate outside the
    # greenlet. A stack trace will be printed to stdout but it
    # will not unwind the stack of the parent.

    print(loser.exception)

    assert True

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import os
import sys

import pg8000

while True:
    try:
        conn = pg8000.connect(host="postgres",
                              user="postgres",
                              password="123456")
    except Exception as e:
        print "wait for postgres to be ready ..."
        time.sleep(1)
    else:
        break

print "postgres connected."

cmd = sys.argv[1]
args = sys.argv[1:]

os.execvp(cmd, args)

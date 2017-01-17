#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time

import mysql.connector

msg_printed = False

while True:
    try:
        cnx = mysql.connector.connect(user='root',
                                      database='fenle_fenqi_db',
                                      host='mysql',
                                      password='123456')
    except mysql.connector.Error:
        if not msg_printed:
            print("wait for mysql to be ready ...")
            msg_printed = True
        time.sleep(1)
    else:
        cnx.close()
        break

print("mysql connected.")

cmd = sys.argv[1]
args = sys.argv[1:]

os.execvp(cmd, args)

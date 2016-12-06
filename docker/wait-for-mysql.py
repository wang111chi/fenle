#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

print "mysql connected."

cmd = sys.argv[1]
args = sys.argv[1:]

os.execvp(cmd, args)

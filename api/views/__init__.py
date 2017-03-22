#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import config

if config.DEBUG:
    __all__ = ("consume", "sms", "layaway",
               "point", "point_cash", "trans", "test")
else:
    __all__ = ("consume", "sms", "layaway",
               "point", "point_cash", "trans")

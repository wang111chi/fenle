#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import os

import config
from base import logger


def init(app):
    app.config.from_object(config)

    # log setting
    logger.init_log([(n, os.path.join("logs", p), l)
                     for n, p, l in config.LOGGING_CONFIG])

# -*- coding: utf-8 -*-

"""
SplitSettings for JIDUI project.

__init__.py merges default.py, <JIDUI_SETTINGS>.py in that order.

default.py is a default config module.

JIDUI_SETTINGS is a env, it can be set in
uwsgi config file:
* local, for development enviroment.
* online, for online enviroment.

"""

import os
from config_global import *


def deep_update(from_dict, to_dict):
    for (key, value) in from_dict.iteritems():
        if key in to_dict.keys() and \
                isinstance(to_dict[key], dict) and \
                isinstance(value, dict):
            deep_update(value, to_dict[key])
        else:
            to_dict[key] = value

modules = ["default"]
env = os.environ.get("JIDUI_SETTINGS")
if env:
    modules.append(env)

current = __name__
for module_name in modules:
    try:
        module = getattr(__import__(current, globals(), locals(),
                                    [module_name]), module_name)
    except AttributeError, e:
        continue

    module_fg = {}
    for fg in dir(module):
        if fg.startswith("__") and fg.endswith("__"):
            continue
        module_fg[fg] = getattr(module, fg)
    deep_update(module_fg, locals())

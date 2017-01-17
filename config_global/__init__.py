# -*- coding: utf-8 -*-

"""
SplitSettings for fenle project.

__init__.py merges default.py, <FENLE_SETTINGS>.py in that order.

default.py is a default config module.

FENLE_SETTINGS is a env, it can be set in
uwsgi config file:
* local, for development enviroment.
* test, for testing environment.
* online, for online enviroment.
"""

import os


def deep_update(from_dict, to_dict):
    for (key, value) in from_dict.items():
        if key in to_dict.keys() and \
                isinstance(to_dict[key], dict) and \
                isinstance(value, dict):
            deep_update(value, to_dict[key])
        else:
            to_dict[key] = value


modules = ["default"]
env = os.environ.get("FENLE_SETTINGS")
if env:
    modules.append(env)

current = __name__

for module_name in modules:
    try:
        module = getattr(__import__(current, globals(), locals(),
                                    [module_name]), module_name)

    except AttributeError:
        continue

    module_fg = {}

    for fg in dir(module):
        if fg.startswith("__") and fg.endswith("__"):
            continue
        module_fg[fg] = getattr(module, fg)
    deep_update(module_fg, locals())
    locals().pop(module_name, None)

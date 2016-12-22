import os
import sys

project_home = os.path.realpath(__file__)
project_home = os.path.split(project_home)[0]

sys.path.insert(0, os.path.split(project_home)[0])
sys.path.insert(0, project_home)

import config
from base import logger

logger.init_log([(n, os.path.join("logs", p), l)
                 for n, p, l in config.LOGGING_CONFIG])

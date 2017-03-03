import os
import sys

project_home = os.path.realpath(__file__)
project_home = os.path.split(project_home)[0]
project_home = os.path.split(project_home)[0]

sys.path.insert(0, os.path.split(project_home)[0])
sys.path.insert(0, project_home)

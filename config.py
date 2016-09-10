import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEBUG = True
BLUBB = '123'

try:
    from config_local import *
except ImportError:
    pass

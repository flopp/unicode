import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEBUG = True

try:
    from config_local import *
except ImportError:
    pass

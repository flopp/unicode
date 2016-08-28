#!/home/flopp/projects/unicode/venv/bin/python3

import sys, os
import logging
from logging.handlers import RotatingFileHandler

PATH = os.path.expanduser("~/projects/unicode/")
sys.path.insert(0, PATH)

from www import app

log_file = os.path.expanduser("~/project-logs/unicode.log")
log = open(log_file, 'w')
log.seek(0)
log.truncate()
log.write("unicode webapp\n")
log.close()

log_handler = RotatingFileHandler(log_file, maxBytes=1000000, backupCount=10)
formatter = logging.Formatter("[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
log_handler.setFormatter(formatter)
app.logger.setLevel(logging.DEBUG)
app.logger.addHandler(log_handler)

from flipflop import WSGIServer
WSGIServer(app).run()

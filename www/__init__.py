from flask import Flask
from flask_caching import Cache

app = Flask(__name__)
app.config.from_object('config')
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

try:
    from flask_compress import Compress
    Compress(app)
except ImportError:
    pass

import www.unicodeapp
import www.error
import www.uinfo

app.uinfo = uinfo.UInfo()


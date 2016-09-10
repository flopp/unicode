from flask import Flask

app = Flask(__name__)
app.config.from_object('config')
app.config['GOOGLE_SITE_VERIFICATION'] = '<meta name="google-site-verification" content="dFepbcMFobUP1XDk52zR2kMAHQE5WFYB0XOAwBapyzE" />'
app.config['PIWIK'] = '''<!-- Piwik -->
<script type="text/javascript">
  var _paq = _paq || [];
  _paq.push(["setDomains", ["*.unicode.flopp.net"]]);
  _paq.push(['trackPageView']);
  _paq.push(['enableLinkTracking']);
  (function() {
    var u="//flopp.grus.uberspace.de/piwik/";
    _paq.push(['setTrackerUrl', u+'piwik.php']);
    _paq.push(['setSiteId', '3']);
    var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0];
    g.type='text/javascript'; g.async=true; g.defer=true; g.src=u+'piwik.js'; s.parentNode.insertBefore(g,s);
  })();
</script>
<noscript><p><img src="//flopp.grus.uberspace.de/piwik/piwik.php?idsite=3" style="border:0;" alt="" /></p></noscript>
<!-- End Piwik Code -->
'''

try:
    from flask_compress import Compress
    Compress(app)
except ImportError:
    pass

import www.unicodeapp
import www.error
import www.uinfo

app.uinfo = uinfo.UInfo()


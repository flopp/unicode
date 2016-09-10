import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEBUG = True

GOOGLE_SITE_VERIFICATION = '''<meta name="google-site-verification" content="dFepbcMFobUP1XDk52zR2kMAHQE5WFYB0XOAwBapyzE" />'''

PIWIK = '''<!-- Piwik -->
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
    from config_local import *
except ImportError:
    pass

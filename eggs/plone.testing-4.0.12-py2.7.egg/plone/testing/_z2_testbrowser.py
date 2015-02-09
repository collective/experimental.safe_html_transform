import sys
import re
import base64
import rfc822
import urllib
import urllib2

from cStringIO import StringIO

import mechanize
import pkg_resources

# Using a from-import here to avoid an AttributeError below when using
# zope.testbrowser 4.x without zope.app.testing:
from zope.testbrowser.testing import PublisherConnection, PublisherResponse
import zope.testbrowser.browser


try:
    pkg_resources.get_distribution('Zope2>=2.13')
    def get_cookies(request):
        return request.response._cookie_list()
except (pkg_resources.VersionConflict, pkg_resources.DistributionNotFound):
    def get_cookies(request):
        return [(c[:10], c[12:]) for c in request.response._cookie_list()]


class Browser(zope.testbrowser.browser.Browser):
    """A test browser client that uses the Zope 2 publisher. It must be
    passed the Zope 2 application root as an argument.
    """

    def __init__(self, app, url=None):
        super(Browser, self).__init__(url=url, mech_browser=Zope2MechanizeBrowser(app))

class Zope2MechanizeBrowser(mechanize.Browser):
    """A mechanize browser class that uses the Zope 2 publisher to talk HTTP
    """

    default_schemes    = ['http']
    default_others     = ['_http_error', '_http_request_upgrade', '_http_default_error']
    default_features   = ['_redirect', '_cookies', '_referer', '_refresh','_equiv', '_basicauth', '_digestauth' ]

    def __init__(self, app, *args, **kws):

        def httpHandlerFactory():
            return Zope2HTTPHandler(app)

        self.handler_classes = mechanize.Browser.handler_classes.copy()
        self.handler_classes["http"] = httpHandlerFactory
        self.default_others = [cls for cls in self.default_others
                               if cls in mechanize.Browser.handler_classes]
        mechanize.Browser.__init__(self, *args, **kws)

class Zope2HTTPHandler(urllib2.HTTPHandler):
    """A protocol handler that uses the Zope 2 publisher to talk HTTP
    """

    def __init__(self, app, debuglevel=0):
        urllib2.HTTPHandler.__init__(self, debuglevel)
        self.app = app

    def http_open(self, req):
        def connectionFactory(host, timeout=None):
            return Zope2Connection(self.app, host, timeout=timeout)
        return self.do_open(connectionFactory, req)

class Zope2Connection(PublisherConnection):
    """A urllib2-compatible connection that can talk to the Zope 2 publisher.
    """

    def __init__(self, app, host, timeout=None):
        self.caller = Zope2Caller(app)
        self.host = host

    def getresponse(self):
        """Return a ``urllib2`` compatible response from the response returned
        by the Zope 2 publisher.
        """

        status = self.response.getStatus()

        import zope.publisher.http
        reason = zope.publisher.http.status_reasons[status]

        headers = []

        # Convert header keys to camel case. This is basically a copy
        # paste from ZPublisher.HTTPResponse
        for key, val in self.response.headers.items():
            if key.lower() == key:
                # only change non-literal header names
                key = "%s%s" % (key[:1].upper(), key[1:])
                start = 0
                l = key.find('-',start)
                while l >= start:
                    key = "%s-%s%s" % (key[:l],key[l+1:l+2].upper(),key[l+2:])
                    start = l + 1
                    l = key.find('-', start)
            headers.append((key, val))

        # Get the cookies, breaking them into tuples for sorting
        cookies = get_cookies(self)
        headers.extend(cookies)
        headers.sort()
        headers.insert(0, ('Status', "%s %s" % (status, reason)))
        headers = '\r\n'.join('%s: %s' % h for h in headers)
        content = self.response.getBody()

        return PublisherResponse(content, headers, status, reason)

def saveState(func):
    """Save threadlocal state (security manager, local component site) before
    exectuting a decorated function, and restore it after.
    """
    from AccessControl.SecurityManagement import getSecurityManager
    from AccessControl.SecurityManagement import setSecurityManager
    from zope.site.hooks import getSite
    from zope.site.hooks import setSite

    def wrapped_func(*args, **kw):
        sm, site = getSecurityManager(), getSite()
        try:
            return func(*args, **kw)
        finally:
            setSecurityManager(sm)
            setSite(site)
    return wrapped_func

HEADER_RE = re.compile('(\S+): (.+)$')
def splitHeader(header):
    return HEADER_RE.match(header).group(1, 2)

BASIC_RE = re.compile('Basic (.+)?:(.+)?$')
def authHeader(header):
    match = BASIC_RE.match(header)
    if match:
        u, p = match.group(1, 2)
        if u is None:
            u = ''
        if p is None:
            p = ''
        auth = base64.encodestring('%s:%s' % (u, p))
        return 'Basic %s' % auth[:-1]
    return header

class Zope2Caller(object):
    """Functional testing caller that can execute HTTP requests via the
    Zope 2 publisher.
    """

    def __init__(self, app):
        self.app = app

    @saveState
    def __call__(self, requestString, handle_errors=True):

        from ZPublisher.Iterators import IStreamIterator
        from ZPublisher.Response import Response
        from ZPublisher.Test import publish_module

        class TestResponse(Response):

            def setBody(self, body, title='', is_error=0, **kw):
                if IStreamIterator.providedBy(body):
                    body = ''.join(body)
                Response.setBody(self, body, title, is_error, **kw)

        # Discard leading white space to make call layout simpler
        requestString = requestString.lstrip()

        # Split off and parse the command line
        l = requestString.find('\n')
        commandLine = requestString[:l].rstrip()
        requestString = requestString[l+1:]
        method, url, protocol = commandLine.split()

        instream = StringIO(requestString)

        env = {"HTTP_HOST": 'localhost',
               "HTTP_REFERER": 'localhost',
               "REQUEST_METHOD": method,
               "SERVER_PROTOCOL": protocol,
               }

        p = url.split('?', 1)
        if len(p) == 1:
            env['PATH_INFO'] = p[0]
        elif len(p) == 2:
            [env['PATH_INFO'], env['QUERY_STRING']] = p
        else:
            raise TypeError, ''

        # If you followed closely, you notice that one part of the url
        # gets unquoted (PATH_INFO) while the other (QUERY_STRING)
        # doesn't That complies with what the ZSERVER does.
        env['PATH_INFO'] = urllib.unquote(env['PATH_INFO'])

        headers = [splitHeader(header) for header in rfc822.Message(instream).headers]

        # Store request body without headers
        instream = StringIO(instream.read())

        for name, value in headers:
            name = ('_'.join(name.upper().split('-')))
            if name not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                name = 'HTTP_' + name
            env[name] = value.rstrip()

        if env.has_key('HTTP_AUTHORIZATION'):
            env['HTTP_AUTHORIZATION'] = authHeader(env['HTTP_AUTHORIZATION'])

        outstream = StringIO()
        response = TestResponse(stdout=outstream, stderr=sys.stderr)

        publish_module('Zope2',
                       response=response,
                       stdin=instream,
                       environ=env,
                       debug=not handle_errors,
                      )

        self.app._p_jar.sync()

        return response

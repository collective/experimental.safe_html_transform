from zope.interface import Interface
from zope import schema

from zope.i18nmessageid import MessageFactory

_ = MessageFactory('plone.cachepurging')

class ICachePurgingSettings(Interface):
    """Settings used by the purging algorithm.

    Should be installed into ``plone.registry``.
    """

    enabled = schema.Bool(
            title=_(u"Enable purging"),
            description=_(u"If disabled, no purging will take place"),
            default=True,
        )

    cachingProxies = schema.Tuple(
            title=_(u"Caching proxies"),
            description=_(u"Provide the URLs of each proxy to which PURGE "
                          u"requests shoudl be sent."),
            value_type=schema.URI(),
        )

    virtualHosting = schema.Bool(
            title=_(u"Send PURGE requests with virtual hosting paths"),
            description=_(u"This option is only relevant if you are using "
                          u"virtual hosting with Zope's VirtualHostMonster. "
                          u"This relies on special tokens (VirtualHostBase "
                          u"and VirtualHostRoot) in the URL to instruct "
                          u"Zope about the types of URLs that the user sees. "
                          u"If virtual host URLs are in use and this option "
                          u"is set, PURGE requests will be sent to the "
                          u"caching proxy with the virtual hosting tokens "
                          u"in place. This makes sense if there is a web "
                          u"server in front of your caching proxy performing "
                          u"the rewrites necessary to translate a user-"
                          u"facing URL into a virtual hosting URL, so that "
                          u"the requests the caching proxy sees have the "
                          u"rewrite information in them. Conversely, if the "
                          u"rewrite is done in or behind the caching proxy, "
                          u"you want to disable this option, so that the "
                          u"PURGE requests use URLs that match those seen "
                          u"by the caching proxy as they come from the "
                          u"client."),
            required=True,
            default=False,
        )

    domains = schema.Tuple(
            title=_(u"Domains"),
            description=_(u"This option is only relevant if you are using "
                          u"virtual hosting and you have enabled the option "
                          u"to send PURGE requests with virtual hosting URLs "
                          u"above. If you your site is served on multiple "
                          u"domains e.g. http://example.org and "
                          u"http://www.example.org you may wish to purge "
                          u"both. If so, list all your domains here"),
            required=False,
            default=(),
            missing_value=(),
            value_type=schema.URI(),
        )

class IPurgePathRewriter(Interface):
    """Used to rewrite paths for purging. This should be registered as an
    adapter on the request.

    The same instance may be re-used several times in the same request.
    """

    def __call__(path):
        """Given a relative path, return a list of paths to purge (e.g. if
        there are multiple variants). The returned paths should not have a
        domain component, but should be relative to the domain root, e.g.
        /path/to/view. Return an empty list if there is nothing to purge.
        """

class IPurger(Interface):
    """A utility used to manage the purging process.
    """

    def purgeAsync(url, httpVerb='PURGE'):
        """Send a PURGE request to a particular URL asynchronously in a
        worker thread.
        """

    def purgeSync(url, httpVerb='PURGE'):
        """Send a PURGE request to a particular URL synchronosly.

        Returns a triple ``(status, xcache, xerror)`` where ``status`` is
        the HTTP status of the purge request, ``xcache`` is the contents of
        the ``x-cache`` response header, and ``x-error`` is the contents
        of the first header found from the list of headers in
        ``errorHeaders``.
        """

    def stopThreads(wait=False):
        """Attempts to stop all threads.  Threads stop immediately after
        the current item is being processed.

        Returns True if successful, or False if threads are still running
        after waiting 5 seconds for each one.
        """

    errorHeaders = schema.Tuple(
            title=u"Error header names",
            value_type=schema.ASCIILine(),
            default=('x-squid-error',)
        )

    http_1_1 = schema.Bool(
            title=u"Use HTTP 1.1 for PURGE request",
            default=True,
        )
import re
import time
import datetime
import logging
import dateutil.parser
import dateutil.tz
import wsgiref.handlers

from thread import allocate_lock

from zope.interface import alsoProvides
from zope.component import queryMultiAdapter
from zope.component import queryUtility
from zope.component import getUtility

from zope.annotation.interfaces import IAnnotations
from z3c.caching.interfaces import ILastModified
from plone.registry.interfaces import IRegistry
from plone.memoize.interfaces import ICacheChooser

from plone.app.caching.interfaces import IRAMCached
from plone.app.caching.interfaces import IETagValue
from plone.app.caching.interfaces import IPloneCacheSettings

from AccessControl.PermissionRole import rolesForPermissionOn
from Products.CMFCore.interfaces import IContentish
from Products.CMFCore.interfaces import ISiteRoot

PAGE_CACHE_KEY = 'plone.app.caching.operations.ramcache'
PAGE_CACHE_ANNOTATION_KEY = 'plone.app.caching.operations.ramcache.key'
ETAG_ANNOTATION_KEY = 'plone.app.caching.operations.etag'
LASTMODIFIED_ANNOTATION_KEY = 'plone.app.caching.operations.lastmodified'
_marker = object()

logger = logging.getLogger('plone.app.caching')

parseETagLock = allocate_lock()
# etagQuote = re.compile('(\s*\"([^\"]*)\"\s*,{0,1})')
# etagNoQuote = re.compile('(\s*([^,]*)\s*,{0,1})')

etagQuote = re.compile('(\s*(W\/)?\"([^\"]*)\"\s*,?)')
etagNoQuote = re.compile('(\s*(W\/)?([^,]*)\s*,?)')

#
# Operation helpers, used in the implementations of interceptResponse() and
# modifyResponse().
#
# These all take three parameters, published, request and response, as well
# as any additional keyword parameters required.
#

def setCacheHeaders(published, request, response, maxage=None, smaxage=None, etag=None, lastModified=None, vary=None):
    """General purpose dispatcher to set various cache headers

    ``maxage`` is the cache timeout value in seconds
    ``smaxage`` is the proxy cache timeout value in seconds.
    ``lastModified`` is a datetime object for the last modified time
    ``etag`` is an etag string
    ``vary`` is a vary header string
    """

    if maxage:
        cacheInBrowserAndProxy(published, request, response, maxage, smaxage=smaxage,
            etag=etag, lastModified=lastModified, vary=vary)

    elif smaxage:
        cacheInProxy(published, request, response, smaxage,
            etag=etag, lastModified=lastModified, vary=vary)

    elif etag or lastModified:
        cacheInBrowser(published, request, response,
            etag=etag, lastModified=lastModified)

    else:
        doNotCache(published, request, response)

def doNotCache(published, request, response):
    """Set response headers to ensure that the response is not cached by
    web browsers or caching proxies.

    This is an IE-safe operation. Under certain conditions, IE chokes on
    ``no-cache`` and ``no-store`` cache-control tokens so instead we just
    expire immediately and disable validation.
    """

    if response.getHeader('Last-Modified'):
        del response.headers['last-modified']

    response.setHeader('Expires', formatDateTime(getExpiration(0)))
    response.setHeader('Cache-Control', 'max-age=0, must-revalidate, private')

def cacheInBrowser(published, request, response, etag=None, lastModified=None):
    """Set response headers to indicate that browsers should cache the
    response but expire immediately and revalidate the cache on every
    subsequent request.

    ``etag`` is a string value indicating an ETag to use.
    ``lastModified`` is a datetime object

    If neither etag nor lastModified is given then no validation is
    possible and this becomes equivalent to doNotCache()
    """

    if etag is not None:
        response.setHeader('ETag', '"%s"' %etag, literal=1)

    if lastModified is not None:
        response.setHeader('Last-Modified', formatDateTime(lastModified))
    elif response.getHeader('Last-Modified'):
        del response.headers['last-modified']

    response.setHeader('Expires', formatDateTime(getExpiration(0)))
    response.setHeader('Cache-Control', 'max-age=0, must-revalidate, private')

def cacheInProxy(published, request, response, smaxage, etag=None, lastModified=None, vary=None):
    """Set headers to cache the response in a caching proxy.

    ``smaxage`` is the timeout value in seconds.
    ``lastModified`` is a datetime object for the last modified time
    ``etag`` is an etag string
    ``vary`` is a vary header string
    """

    if lastModified is not None:
        response.setHeader('Last-Modified', formatDateTime(lastModified))
    elif response.getHeader('Last-Modified'):
        del response.headers['last-modified']

    if etag is not None:
        response.setHeader('ETag', '"%s"' %etag, literal=1)

    if vary is not None:
        response.setHeader('Vary', vary)

    response.setHeader('Expires', formatDateTime(getExpiration(0)))
    response.setHeader('Cache-Control', 'max-age=0, s-maxage=%d, must-revalidate' % smaxage)

def cacheInBrowserAndProxy(published, request, response, maxage, smaxage=None, etag=None, lastModified=None, vary=None):
    """Set headers to cache the response in the browser and caching proxy if
    applicable.

    ``maxage`` is the timeout value in seconds
    ``smaxage`` is the proxy timeout value in seconds
    ``lastModified`` is a datetime object for the last modified time
    ``etag`` is an etag string
    ``vary`` is a vary header string
    """

    if lastModified is not None:
        response.setHeader('Last-Modified', formatDateTime(lastModified))
    elif response.getHeader('Last-Modified'):
        del response.headers['last-modified']

    if etag is not None:
        response.setHeader('ETag', '"%s"' %etag, literal=1)

    if vary is not None:
        response.setHeader('Vary', vary)

    response.setHeader('Expires', formatDateTime(getExpiration(maxage)))

    if smaxage is not None:
        maxage = '%s, s-maxage=%s' %(maxage, smaxage)

    # Substituting proxy-validate in place of must=revalidate here because of Safari bug
    # https://bugs.webkit.org/show_bug.cgi?id=13128
    response.setHeader('Cache-Control', 'max-age=%s, proxy-revalidate, public' % maxage)

def cacheInRAM(published, request, response, etag=None, lastModified=None, annotationsKey=PAGE_CACHE_ANNOTATION_KEY):
    """Set a flag indicating that the response for the given request
    should be cached in RAM.

    This will signal to a transform chain step after the response has been
    generated to store the result in the RAM cache.

    To actually use the cached response, you can implement
    ``interceptResponse()`` in your caching operation to call
    ``fetchFromRAMCache()`` and then return the value of the
    ``cachedResponse()`` helper.

    ``etag`` is a string identifying the resource.

    ``annotationsKey`` is the key used by the transform to look up the
    caching key when storing the response in the cache. It should match that
    passed to ``storeResponseInRAMCache()``.
    """

    annotations = IAnnotations(request, None)
    if annotations is None:
        return None

    key = getRAMCacheKey(request, etag=etag, lastModified=lastModified)

    annotations[annotationsKey] = key
    alsoProvides(request, IRAMCached)

def cachedResponse(published, request, response, status, headers, body, gzip=False):
    """Returned a cached page. Modifies the response (status and headers)
    and returns the cached body.

    ``status`` is the cached HTTP status
    ``headers`` is a dictionary of cached HTTP headers
    ``body`` is a cached response body
    ``gzip`` should be set to True if the response is to be gzipped
    """

    response.setStatus(status)

    for k, v in headers.items():
        if k.lower() == 'etag':
            response.setHeader(k, v, literal=1)
        else:
            response.setHeader(k, v)

    response.setHeader('X-RAMCache', PAGE_CACHE_KEY, literal=1)

    if not gzip:
        response.enableHTTPCompression(request, disable=True)
    else:
        response.enableHTTPCompression(request)

    return body

def notModified(published, request, response, etag=None, lastModified=None):
    """Return a ``304 NOT MODIFIED`` response. Modifies the response (status)
    and returns an empty body to indicate the request should be interrupted.

    ``etag`` is an ETag to set on the response
    ``lastModified`` is the last modified date to set on the response

    Both ``etag`` and ``lastModified`` are optional.
    """

    if etag is not None:
        response.setHeader('ETag', etag, literal=1)

    # Specs say that Last-Modified MUST NOT be included in a 304
    # and Cache-Control/Expires MUST NOT be included unless they
    # differ from the original response.  We'll delete all, including
    # Expires although technically it should be included.  This is
    # probably okay since in the original we only include Expires
    # along with a Cache-Control and HTTP/1.1 clients will always
    # use the later over any Expires header anyway.  HTTP/1.0 clients
    # never send conditional requests so they will never see this.
    #
    # http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
    #
    if response.getHeader('Last-Modified'):
        del response.headers['last-modified']
    if response.getHeader('Expires'):
        del response.headers['expires']
    if response.getHeader('Cache-Control'):
        del response.headers['cache-control']

    response.setStatus(304)
    return u""


#
# Cache checks
#

def cacheStop(request, rulename):
    """Check for any cache stop variables in the request.
    """

    # Only cache GET requests
    if request.get('REQUEST_METHOD') != 'GET':
        return True

    # rss_search also uses the SearchableText variable
    # so we'll hard code an exception for now
    if rulename == 'plone.content.feed':
        return False

    registry = getUtility(IRegistry)
    if registry is None:
        return False

    ploneSettings = registry.forInterface(IPloneCacheSettings)
    variables = ploneSettings.cacheStopRequestVariables

    for variable in variables:
        if request.has_key(variable):
            return True
    return False

def isModified(request, etag=None, lastModified=None):
    """Return True or False depending on whether the published resource has
    been modified.

    ``etag`` is the current etag, to be checked against the If-None-Match
    header.

    ``lastModified`` is the current last-modified datetime, to be checked
    against the If-Modified-Since header.
    """

    if not etag and not lastModified:
        return True

    ifModifiedSince = request.getHeader('If-Modified-Since', None)
    ifNoneMatch = request.getHeader('If-None-Match', None)

    if ifModifiedSince is None and ifNoneMatch is None:
        return True

    etagMatched = False

    # Check etags
    if ifNoneMatch and etag is not None:
        if not etag:
            return True

        clientETags = parseETags(ifNoneMatch)
        if not clientETags:
            return True

        # is the current etag in the list of client-side etags?
        if etag not in clientETags and '*' not in clientETags:
            return True

        etagMatched = True

    """
    If a site turns off etags after having them on, the pages previously
    served will return an If-None-Match header, but the site will not be 
    configured for etags. In this case, force a refresh to load the 
    latest headers. I interpret this as the spec rule that the 
    etags do NOT match, and therefor we must not return a 304.
    """
    if ifNoneMatch and etag==None:
        return True

    # Check the modification date
    if ifModifiedSince and lastModified is not None:

        # Attempt to get a date

        ifModifiedSince = ifModifiedSince.split(';')[0]
        ifModifiedSince = parseDateTime(ifModifiedSince)

        if ifModifiedSince is None:
            return True

        # has content been modified since the if-modified-since time?
        try:
            # browser only knows the date to one second resolution
            if (lastModified - ifModifiedSince) > datetime.timedelta(seconds=1):
                return True
        except TypeError:
            logger.exception("Could not compare dates")

        # If we expected an ETag and the client didn't give us one, consider
        # that an error. This may be more conservative than the spec requires.
        if etag is not None:
            if not etagMatched:
                return True

    # XXX Do we really want the default here to be false?
    return False

 
def visibleToRole(published, role, permission='View'):
    """Determine if the published object would be visible to the given
    role.

    ``role`` is a role name, e.g. ``Anonymous``.
    ``permission`` is the permission to check for.
    """
    return role in rolesForPermissionOn(permission, published)

#
# Basic helper functions
#

def getContext(published, marker=(IContentish, ISiteRoot,)):
    """Given a published object, attempt to look up a context

    ``published`` is the object that was published.
    ``marker`` is a marker interface to look for

    Returns an item providing ``marker`` or None, if it cannot be found.
    """

    if not isinstance(marker, (list, tuple,)):
        marker = (marker,)

    def checkType(context):
        for m in marker:
            if m.providedBy(context):
                return True
        return False

    while (
        published is not None
        and not checkType(published)
        and hasattr(published, '__parent__',)
    ):
        published = published.__parent__

    if not checkType(published):
        return None

    return published

def formatDateTime(dt):
    """Format a Python datetime object as an RFC1123 date.

    If the datetime object is timezone-naive, it is assumed to be local time.
    """

    # We have to pass local time to format_date_time()

    if dt.tzinfo is not None:
        dt = dt.astimezone(dateutil.tz.tzlocal())

    return wsgiref.handlers.format_date_time(time.mktime(dt.timetuple()))

def parseDateTime(str):
    """Return a Python datetime object from an an RFC1123 date.

    Returns a datetime object with a timezone. If no timezone is found in the
    input string, assume local time.
    """

    try:
        dt = dateutil.parser.parse(str)
    except ValueError:
        return None

    if not dt:
        return None

    if dt.tzinfo is None:
        dt = datetime.datetime(dt.year, dt.month, dt.day,
                               dt.hour, dt.minute, dt.second, dt.microsecond,
                               dateutil.tz.tzlocal())

    return dt

def getLastModifiedAnnotation(published, request, lastModified=True):
    """Try to get the last modified date from a request annotation if available,
    otherwise try to get it from published object
    """

    if not lastModified:
        return None

    annotations = IAnnotations(request, None)
    if annotations is not None:
        dt = annotations.get(LASTMODIFIED_ANNOTATION_KEY, _marker)
        if dt is not _marker:
            return dt

    dt = getLastModified(published, lastModified=lastModified)

    if annotations is not None:
        annotations[LASTMODIFIED_ANNOTATION_KEY] = dt

    return dt

def getLastModified(published, lastModified=True):
    """Get a last modified date or None.

    If an ``ILastModified`` adapter can be found, and returns a date that is
    not timezone aware, assume it is local time and add timezone.
    """

    if not lastModified:
        return None

    lastModified = ILastModified(published, None)
    if lastModified is None:
        return None

    dt = lastModified()
    if dt is None:
        return None

    if dt.tzinfo is None:
        dt = datetime.datetime(dt.year, dt.month, dt.day,
                               dt.hour, dt.minute, dt.second, dt.microsecond,
                               dateutil.tz.tzlocal())

    return dt

def getExpiration(maxage):
    """Get an expiration date as a datetime in the local timezone.

    ``maxage`` is the maximum age of the item, in seconds. If it is 0 or
    negative, return a date ten years in the past.
    """

    now = datetime.datetime.now()
    if maxage > 0:
        return now + datetime.timedelta(seconds=maxage)
    else:
        return now - datetime.timedelta(days=3650)

def getETagAnnotation(published, request, keys=(), extraTokens=()):
    """Try to get the ETag from a request annotation if available,
    otherwise try to get it from published object
    """

    if not keys and not extraTokens:
        return None

    annotations = IAnnotations(request, None)
    if annotations is not None:
        etag = annotations.get(ETAG_ANNOTATION_KEY, _marker)
        if etag is not _marker:
            return etag

    etag = getETag(published, request, keys=keys, extraTokens=extraTokens)

    if annotations is not None:
        annotations[ETAG_ANNOTATION_KEY] = etag

    return etag

def getETag(published, request, keys=(), extraTokens=()):
    """Calculate an ETag.

    ``keys`` is a list of types of items to include in the ETag. These must
    match named multi-adapters on (published, request) providing
    ``IETagValue``.

    ``extraTokens`` is a list of additional ETag tokens to include, verbatim
    as strings.

    All tokens will be concatenated into an ETag string, separated by pipes.
    """

    if not keys and not extraTokens:
        return None

    tokens = []
    noTokens = True
    for key in keys:
        component = queryMultiAdapter((published, request), IETagValue, name=key)
        if component is None:
            logger.warning("Could not find value adapter for ETag component %s", key)
            tokens.append('')
        else:
            value = component()
            if value is None:
                value = ''
            else:
                noTokens = False
            tokens.append(value)

    for token in extraTokens:
        noTokens = False
        tokens.append(token)

    if noTokens:
        return None

    etag = '|' + '|'.join(tokens)
    etag = etag.replace(',', ';')  # commas are bad in etags
    etag = etag.replace('"', "'")  # double quotes are bad in etags

    return etag

def parseETags(text, allowWeak=True, _result=None):
    """Parse a header value into a list of etags. Handles fishy quoting and
    other browser quirks.

    ``text`` is the header value to parse.
    ``allowWeak`` should be False if weak ETag values should not be returned
    ``_result`` is internal - don't set it.

    Returns a list of strings. For weak etags, the W/ prefix is removed.
    """

    result = _result

    if result is None:
        result = []

    if not text:
        return result

    # Lock, since regular expressions are not threadsafe
    parseETagLock.acquire()
    try:
        m = etagQuote.match(text)
        if m:
            # Match quoted etag (spec-observing client)
            l     = len(m.group(1))
            value = (m.group(2) or '') + (m.group(3) or '')
        else:
            # Match non-quoted etag (lazy client)
            m = etagNoQuote.match(text)
            if m:
                l     = len(m.group(1))
                value = (m.group(2) or '') + (m.group(3) or '')
            else:
                return result
    finally:
        parseETagLock.release()

    if value:

        if value.startswith('W/'):
            if allowWeak:
                result.append(value[2:])
        else:
            result.append(value)

    return parseETags(text[l:], allowWeak=allowWeak, _result=result)

#
# RAM cache management
#

def getRAMCache(globalKey=PAGE_CACHE_KEY):
    """Get a RAM cache instance for the given key. The return value is ``None``
    if no RAM cache can be found, or a mapping object supporting at least
    ``__getitem__()``, ``__setitem__()`` and ``get()`` that can be used to get
    or set cache values.

    ``key`` is the global cache key, which must be unique site-wide. Most
    commonly, this will be the operation dotted name.
    """

    chooser = queryUtility(ICacheChooser)
    if chooser is None:
        return None

    return chooser(globalKey)

def getRAMCacheKey(request, etag=None, lastModified=None):
    """Calculate the cache key for pages cached in RAM.

    ``etag`` is a unique etag string.

    ``lastModified`` is a datetime object giving the last=modified
     date for the resource.

    The cache key is a combination of the resource's URL, the etag,
    and the last-modified date. Both the etag and last=modified are
    optional but in most cases that are worth caching in RAM, the etag
    is needed to ensure the key changes when the resource view changes.
    """

    resourceKey = "%s%s?%s" % (
        request.get('SERVER_URL', ''),
        request.get('PATH_INFO', ''),
        request.get('QUERY_STRING', ''),
        )
    if etag:
        resourceKey = '|' + etag + '||' + resourceKey
    if lastModified:
        resourceKey = '|' + str(lastModified) + '||' + resourceKey
    return resourceKey

def storeResponseInRAMCache(request, response, result, globalKey=PAGE_CACHE_KEY, annotationsKey=PAGE_CACHE_ANNOTATION_KEY):
    """Store the given response in the RAM cache.

    ``result`` should be the response body as a string.

    ``globalKey`` is the global cache key. This needs to be the same key
    as the one used to fetch the data.

    ``annotationsKey`` is the key in annotations on the request from which
    the (resource-identifying) caching key should be retrieved. The default
    is that used by the ``cacheInRAM()`` helper function.
    """

    annotations = IAnnotations(request, None)
    if annotations is None:
        return

    key = annotations.get(annotationsKey)
    if not key:
        return

    cache = getRAMCache(globalKey)
    if cache is None:
        return
    
    """
    Resource registries have no body. If we put them in the cache the content 
    type headers will indicate length and the body will be '', causing the browser 
    to just spin. Furthermore, I doubt we ever want to cache an empty result:
    it's an indication that something went wrong somewhere.

    This does mean that any resources will not be cached in ram. There is 
    potentially another fix but I doubt long term it's ever the right thing to 
    do.
    """
    if result == '':
        return 

    status = response.getStatus()
    headers = dict(request.response.headers)
    gzipFlag = response.enableHTTPCompression(query=True)

    cache[key] = (status, headers, result, gzipFlag)

def fetchFromRAMCache(request, etag=None, lastModified=None, globalKey=PAGE_CACHE_KEY, default=None):
    """Return a page cached in RAM, or None if it cannot be found.

    The return value is a tuple as stored by ``storeResponseInRAMCache()``.

    ``etag`` is an ETag for the content, and is usually used as a basis for
    the cache key.

    ``lastModified`` is the last modified date for the content, which can
    potentially be used instead of etag if sufficient to ensure freshness.
    Perhaps a rare occurance but it's here in case someone needs it.
    Do not use this to cache binary responses (like images and file downloads)
    as Zope already caches most of the payload of these.

    ``globalKey`` is the global cache key. This needs to be the same key
    as the one used to store the data, i.e. it must correspond to the one
    used when calling ``storeResponseInRAMCache()``.
    """

    cache = getRAMCache(globalKey)
    if cache is None:
        return None

    key = getRAMCacheKey(request, etag=etag, lastModified=lastModified)
    if key is None:
        return None

    return cache.get(key, default)

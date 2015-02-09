import re

from Acquisition import aq_base
from ZPublisher.BaseRequest import RequestContainer
from ZPublisher.Publish import dont_publish_class
from ZPublisher.Publish import missing_name
from ZPublisher.mapply import mapply
from cStringIO import StringIO
from logging import getLogger
from posixpath import normpath
from urlparse import urlsplit, urljoin
from urllib import unquote # Python2.4 does not have urlparse.unquote
from zope.interface import alsoProvides
from zope.globalrequest import getRequest, setRequest
try:
    from zope.site.hooks import getSite, setSite
except ImportError:
    from zope.app.component.hooks import getSite, setSite

from plone.subrequest.subresponse import SubResponse
from plone.subrequest.interfaces import ISubRequest

__all__ = ['subrequest', 'SubResponse']

# http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html
CONDITIONAL_HEADERS = [
    'HTTP_IF_MODIFIED_SINCE',
    'HTTP_IF_UNMODIFIED_SINCE',
    'HTTP_IF_MATCH',
    'HTTP_IF_NONE_MATCH',
    'HTTP_IF_RANGE',
    'HTTP_RANGE', # Not strictly a conditional header, but scrub it anyway
    ]

OTHER_IGNORE = set([
    'ACTUAL_URL',
    'LANGUAGE_TOOL',
    'PARENTS',
    'PARENT_REQUEST',
    'PUBLISHED',
    'RESPONSE',
    'SERVER_URL',
    'TraversalRequestNameStack',
    'URL',
    'VIRTUAL_URL',
    'VIRTUAL_URL_PARTS',
    'VirtualRootPhysicalPath',
    'method',
    'traverse_subpath',
    ])

OTHER_IGNORE_RE = re.compile(r'^(?:BASE|URL)\d+$')

logger = getLogger("plone.subrequest")

def subrequest(url, root=None, stdout=None):
    assert url is not None, "You must pass a url"
    if isinstance(url, unicode):
        url = url.encode('utf-8')
    _, _, path, query, _ = urlsplit(url)
    parent_request = getRequest()
    assert parent_request is not None, "Unable to get request, perhaps zope.globalrequest is not configured."
    parent_site = getSite()
    parent_app = parent_request.PARENTS[-1]
    if path.startswith('/'):
        path = normpath(path)
        vurl_parts = parent_request.get('VIRTUAL_URL_PARTS')
        if vurl_parts is not None:
            # Use the virtual host root
            path_past_root = unquote(vurl_parts[-1])
            root_path = normpath(parent_request['PATH_INFO']).rstrip('/')[:-len(path_past_root) or None]
            if root is None:
                path = root_path + path
            else:
                path = '%s/%s%s' % (root_path, root.virtual_url_path(), path)
        elif root is not None:
            path = '/%s%s' % (root.virtual_url_path(), path)
    else:
        try:
            parent_url = parent_request['URL']
            if isinstance(parent_url, unicode):
                parent_url = parent_url.encode('utf-8')
            # extra is the hidden part of the url, e.g. a default view
            extra = unquote(parent_url[len(parent_request['ACTUAL_URL']):])
        except KeyError:
            extra = ''
        here = parent_request['PATH_INFO'] + extra
        path = urljoin(here, path)
        path = normpath(path)
    request = parent_request.clone()
    for name, parent_value in parent_request.other.items():
        if name in OTHER_IGNORE or OTHER_IGNORE_RE.match(name) or name.startswith('_'):
            continue
        request.other[name] = parent_value
    request['PARENT_REQUEST'] = parent_request
    alsoProvides(request, ISubRequest)
    try:
        setRequest(request)
        request_container = RequestContainer(REQUEST=request)
        app = aq_base(parent_app).__of__(request_container)
        request['PARENTS'] = [app]
        response = request.response
        response.__class__ = SubResponse
        response.stderr = None # only used on retry it seems
        if stdout is None:
            stdout = StringIO() # It might be possible to optimize this
        response.stdout = stdout
        environ = request.environ
        environ['PATH_INFO'] = path
        environ['QUERY_STRING'] = query
        # Clean up the request.
        for header in CONDITIONAL_HEADERS:
            environ.pop(header, None)
        try:
            request.processInputs()
            traversed = request.traverse(path)
            result = mapply(traversed, positional=request.args,
                            keyword=request,
                            debug=None,
                            maybe=1,
                            missing_name=missing_name,
                            handle_class=dont_publish_class,
                            context=request,
                            bind=1)
            if result is not response:
                response.setBody(result)
            for key, value in request.response.cookies.items():
                parent_request.response.cookies[key] = value
        except:
            logger.exception("Error handling subrequest to %s" % url)
            response.exception()
        return response
    finally:
        request.clear()
        setRequest(parent_request)
        setSite(parent_site)

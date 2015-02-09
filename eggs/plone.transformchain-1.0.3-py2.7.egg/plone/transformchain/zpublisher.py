import sys
import re

from zope.interface import Interface
from zope.interface.interfaces import IInterface
from zope.component import queryUtility, adapter

from ZPublisher.Iterators import IStreamIterator
from ZPublisher.HTTPResponse import default_encoding

from plone.transformchain.interfaces import ITransformer

from ZPublisher.interfaces import IPubBeforeCommit

try:
    from ZPublisher.interfaces import IPubBeforeAbort
except ImportError:
    # old Zope 2.12 or old ZPublisherBackport - this interface won't be
    # used, most likely, so the effect is that error messages aren't styled.
    class IPubBeforeAbort(Interface):
        pass

CHARSET_RE = re.compile(r'(?:application|text)/[-+0-9a-z]+\s*;\s?charset=([-_0-9a-z]+)(?:(?:\s*;)|\Z)', re.IGNORECASE)

def extractEncoding(response):
    """Get the content encoding for the response body
    """
    encoding = default_encoding
    ct = response.headers.get('content-type')
    if ct:
        match = CHARSET_RE.match(ct)
        if match:
            encoding = match.group(1)
    return encoding

def isEvilWebDAVRequest(request):
    if request.get('WEBDAV_SOURCE_PORT', None):
        return True

    if request.get('REQUEST_METHOD', 'GET').upper() not in ('GET', 'POST',):
        return True

    if request.get('PATH_INFO', '').endswith('manage_DAVget'):
        return True

    return False

def applyTransform(request, body=None):
    """Apply any transforms by delegating to the ITransformer utility
    """

    if isEvilWebDAVRequest(request):
        return None

    transformer = queryUtility(ITransformer)
    if transformer is not None:
        response = request.response
        encoding = extractEncoding(response)

        if body is None:
            body = response.getBody()

        result = body
        if isinstance(result, str):
            result = [result]
        elif isinstance(result, unicode):
            result = [result.encode(encoding)]

        transformed = transformer(request, result, encoding)
        if transformed is not None and transformed is not result:
            return transformed

    return None

@adapter(IPubBeforeCommit)
def applyTransformOnSuccess(event):
    """Apply the transform after a successful request
    """
    transformed = applyTransform(event.request)
    if transformed is not None:
        response = event.request.response

        # horrid check to deal with Plone 3/Zope 2.10, where this is still an old-style interface
        if ((IInterface.providedBy(IStreamIterator)     and IStreamIterator.providedBy(transformed))
         or (not IInterface.providedBy(IStreamIterator) and IStreamIterator.isImplementedBy(transformed))
        ):
            response.setBody(transformed)
        # setBody() can deal with byte and unicode strings (and will encode as necessary)...
        elif isinstance(transformed, basestring):
            response.setBody(transformed)
        # ... but not with iterables
        else:
            response.setBody(''.join(transformed))

@adapter(IPubBeforeAbort)
def applyTransformOnFailure(event):
    """Apply the transform to the error html output
    """
    if not event.retry:
        request = event.request
        exc_info = sys.exc_info()
        error = exc_info[1]
        if isinstance(error, basestring): # Zope 2.10 - the exception is rendered (eeeeek)
            transformed = applyTransform(request, error)
            if transformed is not None:

                if not isinstance(transformed, basestring):
                    transformed = ''.join(transformed)

                # If it's any consolation, Laurence felt quite dirty doing this...
                raise exc_info[0], transformed, exc_info[2]
        else: # Zope 2.12 - we are allowed to call setBody()
            # response.status might still be 200 because
            # IPubBeforeAbort is notified before
            # ZPublisher.Publish.publish_module_standard
            # calls HTTPResponse.exception()
            # which actually updates the status
            setErrorStatusOnResponse(event)
            applyTransformOnSuccess(event)


def setErrorStatusOnResponse(event):
    error_class = event.exc_info[0]
    event.request.response.setStatus(error_class)

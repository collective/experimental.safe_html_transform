import logging

from zope.interface import implements
from zope.interface import Interface
from zope.interface import alsoProvides

from zope.component import adapts, adapter

from zope.globalrequest import getRequest

from ZPublisher.interfaces import IPubAfterTraversal
from ZPublisher.interfaces import IPubBeforeStreaming
from ZODB.POSException import ConflictError

from plone.transformchain.interfaces import ITransform
from plone.transformchain.interfaces import DISABLE_TRANSFORM_REQUEST_KEY

from plone.caching.interfaces import X_CACHE_RULE_HEADER
from plone.caching.interfaces import X_CACHE_OPERATION_HEADER

from plone.caching.utils import findOperation

logger = logging.getLogger('plone.caching')

class IStreamedResponse(Interface):
    """Marker applied when we intercepted a streaming response. This allows
    us to avoid applying the same rules twice, since the normal hook may also
    be executed for streaming responses (albeit on a seemingly empty body,
    and after the response has been sent).
    """

class Intercepted(Exception):
    """Exception raised in order to abort regular processing before the
    published resource (e.g. a view) is called, and render a specific response
    body and status provided by an intercepting caching operation instead.
    """
    
    responseBody = None
    status = None
    
    def __init__(self, status=304, responseBody=u""):
        self.status = status
        self.responseBody = responseBody

class InterceptorResponse(object):
    """View for the Intercepted exception, serving to return an empty
    response in the case of an intercepted response.
    """
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
        
    def __call__(self):
        return self.context.responseBody

@adapter(IPubAfterTraversal)
def intercept(event):
    """Invoke the interceptResponse() method of a caching operation, if one
    can be found.
    
    To properly abort request processing, this will raise an exception. The
    actual response (typically an empty response) is then set via a view on
    the exception. We set and lock the response status to avoid defaulting to
    a 404 exception.
    """
    
    try:
        request = event.request
        published = request.get('PUBLISHED', None)
        
        rule, operationName, operation = findOperation(request)
        
        if rule is None:
            return
        
        request.response.setHeader(X_CACHE_RULE_HEADER, rule)
        logger.debug("Published: %s Ruleset: %s Operation: %s", repr(published), rule, operation)
        
        if operation is not None:
            
            responseBody = operation.interceptResponse(rule, request.response)
            
            if responseBody is not None:
                
                # Only put this in the response if the operation actually
                # intercepted something
                
                request.response.setHeader(X_CACHE_OPERATION_HEADER, operationName)
                
                # Stop any post-processing, including the operation's response
                # modification
                if DISABLE_TRANSFORM_REQUEST_KEY not in request.environ:
                    request.environ[DISABLE_TRANSFORM_REQUEST_KEY] = True
                
                # The view is liable to have set a response status. Lock it
                # now so that it doesn't get set to 500 later.
                status = request.response.getStatus()
                if status:
                    request.response.setStatus(status, lock=True)

                raise Intercepted(status, responseBody)
    
    except ConflictError:
        raise
    except Intercepted:
        raise
    except:
        logging.exception("Swallowed exception in plone.caching IPubAfterTraversal event handler")

class MutatorTransform(object):
    """Transformation using plone.transformchain.
    
    This is registered at order 12000, i.e. "late". A typical transform
    chain order may include:
    
    * lxml transforms (e.g. plone.app.blocks, collectivexdv) => 8000-8999
    * gzip => 10000
    * caching => 12000
    
    This transformer is uncommon in that it doesn't actually change the
    response body. Instead, we look up caching operations which can modify
    response headers and perform other caching functions.
    """
    
    implements(ITransform)
    adapts(Interface, Interface)
    
    order = 12000
    
    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def transformUnicode(self, result, encoding):
        self.mutate()
        return None
    
    def transformBytes(self, result, encoding):
        self.mutate()
        return None
    
    def transformIterable(self, result, encoding):
        self.mutate()
        return None
    
    def mutate(self):
        
        request = self.request
        
        # Abort if this was a streamed request handled by our event handler
        # below
        if IStreamedResponse.providedBy(request):
            return
        
        published = request.get('PUBLISHED', None)
        
        rule, operationName, operation = findOperation(request)
        
        if rule is None:
            return
        
        request.response.setHeader(X_CACHE_RULE_HEADER, rule)
        logger.debug("Published: %s Ruleset: %s Operation: %s", repr(published), rule, operation)
        
        if operation is not None:
            
            request.response.setHeader(X_CACHE_OPERATION_HEADER, operationName)
            operation.modifyResponse(rule, request.response)

# Hook for streaming responses - does not use plone.transformchain, since
# sequencing is less likely to be an issue here

@adapter(IPubBeforeStreaming)
def modifyStreamingResponse(event):
    """Invoke the modifyResponse() method of a caching operation, if one
    can be found, for a streaming response (one using response.write()).
    """
    
    response = event.response
    if response is None:
        return
    
    request = getRequest()
    if request is None:
        return
    
    # Mark the response to allow us to avoid attempting a modify operation
    # again in the normal hook above
    alsoProvides(request, IStreamedResponse)
    
    published = request.get('PUBLISHED', None)
    
    rule, operationName, operation = findOperation(request)
    
    if rule is None:
        return
    
    response.setHeader(X_CACHE_RULE_HEADER, rule)
    logger.debug("Published: %s Ruleset: %s Operation: %s", repr(published), rule, operation)
    
    if operation is not None:
        
        response.setHeader(X_CACHE_OPERATION_HEADER, operationName)
        operation.modifyResponse(rule, response)

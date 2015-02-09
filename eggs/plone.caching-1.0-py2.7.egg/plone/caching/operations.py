from zope.interface import implements, classProvides, Interface
from zope.component import adapts, queryMultiAdapter

from plone.caching.interfaces import ICachingOperation
from plone.caching.interfaces import ICachingOperationType
from plone.caching.interfaces import _

from plone.caching.utils import lookupOptions

class Chain(object):
    """Caching operation which chains together several other operations.
    
    When intercepting the response, the first chained operation to return a
    value will be used. Subsequent operations are ignored. When modifying the
    response, all operations will be called, in order.
    
    The names of the operations to execute are found in the ``plone.registry``
    option ``plone.caching.operations.chain.operations`` by default, and can
    be customised on a per-rule basis with
    ``plone.caching.operations.chain.${rulename}.chain``.
    
    The option must be a sequence type (e.g. a ``Tuple``).
    """
    
    implements(ICachingOperation)
    adapts(Interface, Interface)
    
    # Type metadata
    classProvides(ICachingOperationType)
    
    title = _(u"Chain")
    description = _(u"Allows multiple operations to be chained together")
    prefix = 'plone.caching.operations.chain'
    options = ('operations',)
    
    def __init__(self, published, request):
        self.published = published
        self.request = request

    def interceptResponse(self, rulename, response):
        options = lookupOptions(self.__class__, rulename)
        
        chained = []
        
        if options['operations']:
            for name in options['operations']:
                
                operation = queryMultiAdapter((self.published, self.request),
                                             ICachingOperation, name=name)
                
                if operation is not None:
                    chained.append(name)
                    
                    value = operation.interceptResponse(rulename, response)
                    if value is not None:
                        response.setHeader('X-Cache-Chain-Operations', '; '.join(chained))
                        return value
    
    def modifyResponse(self, rulename, response):
        options = lookupOptions(self.__class__, rulename)
        
        chained = []
        
        if options['operations']:
            for name in options['operations']:
                
                operation = queryMultiAdapter((self.published, self.request),
                                             ICachingOperation, name=name)
                
                if operation is not None:
                    chained.append(name)
                    operation.modifyResponse(rulename, response)

        if chained:
            response.setHeader('X-Cache-Chain-Operations', '; '.join(chained))

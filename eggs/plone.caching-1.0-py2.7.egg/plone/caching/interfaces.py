import zope.i18nmessageid

from zope.interface import Interface
from zope import schema

_ = zope.i18nmessageid.MessageFactory('plone.caching')

X_CACHE_RULE_HEADER      = 'X-Cache-Rule'
X_CACHE_OPERATION_HEADER = 'X-Cache-Operation'

class ICacheSettings(Interface):
    """Settings expected to be found in plone.registry
    """
    
    enabled = schema.Bool(
            title=_(u"Globally enabled"),
            description=_(u"If not set, no caching operations will be attempted"),
            default=False,
        )
    
    operationMapping = schema.Dict(
            title=_(u"Rule set/operation mapping"),
            description=_(u"Maps rule set names to operation names"),
            key_type=schema.DottedName(title=_(u"Rule set name")),
            value_type=schema.DottedName(title=_(u"Caching operation name")),
        )

#
#  Cache operations
# 

class ICachingOperation(Interface):
    """Represents a caching operation, typically setting of response headers
    and/or returning of an intercepted response.
    
    Should be registered as a named multi-adapter from a cacheable object
    (e.g. a view, or just Interface for a general operation) and the request.
    """
    
    def interceptResponse(ruleset, response):
        """Intercept the response if appropriate.
        
        May modify the response if required, e.g. by setting headers.
        
        Return None if the request should *not* be interrupted. Otherwise,
        return a new response body as a unicode string. For simple 304
        responses, returning ``u""`` will suffice.
        
        ``rulset`` is the name of the caching ruleset that was matched. It may
        be ``None``. ``response`` is the current HTTP response.
        
        The response body should *not* be modified.
        """
    
    def modifyResponse(ruleset, response):
        """Modify the response. ``rulset`` is the name of the caching ruleset
        that was matched. It may be ``None``. ``response`` is the current
        HTTP response. You may modify its headers and inspect it as required.
        
        The response body should *not* be modified. If you need to do that,
        either use ``plone.transformchain`` to add a new transformer, or use
        the ``interceptResponse()`` method.
        """


#
# Cache operation *types* (for UI support)
# 

class ICachingOperationType(Interface):
    """A named utility which is used to provide UI support for caching
    operations. The name should correspond to the operation adapter name.
    
    The usual pattern is::
    
        from zope.interface import implements, classProvides, Interface
        from zope.component import adapts
    
        from plone.caching.interfaces import ICachingOperation
        from plone.caching.interfaces import ICachingOperationType
        
        from plone.caching.utils import lookupOptions
        
        class SomeOperation(object):
            implements(ICachingOperation)
            adapts(Interface, Interface)
            
            classProvides(ICachingOperationType)
            title = u"Some operation"
            description = u"Operation description"
            prefix = 'my.package.operation1'
            options = ('option1', 'option2')
            
            def __init__(self, published, request):
                self.published = published
                self.request = request
            
            def __call__(self, rulename, response):
                options = lookupOptions(SomeOperation, rulename)
                ...
        
    This defines an adapter factory (the class), which itself provides
    information about the type of operation. In ZCML, these would be
    registered with::
        
        <adapter factory=".ops.SomeOperation" name="my.package.operation1" />
        <utility component=".ops.SomeOperation" name="my.package.operation1" />
    
    Note that the use of *component* for the ``<utility />`` registration - we
    are registering the class as a utility. Also note that the utility and
    adapter names must match. By convention, the option prefix should be the
    same as the adapter/utility name.
    
    You could also register an instance as a utility, of course.
    """
    
    title = schema.TextLine(
            title=_(u"Title"),
            description=_(u"A descriptive title for the operation"),
        )
    
    description = schema.Text(
            title=_(u"Description"),
            description=_(u"A longer description for the operaton"),
            required=False,
        )
    
    prefix = schema.DottedName(
            title=_(u"Registry prefix"),
            description=_(u"Prefix for records in the registry pertaining to "
                          u"this operation. This, alongside the next "
                          u"parameter, allows the user interface to present "
                          u"relevant configuration options for this "
                          u"operation."),
            required=False, 
        )
    
    options = schema.Tuple(
            title=_(u"Registry options"),
            description=_(u"A tuple of options which can be used to "
                          u"configure this operation. An option is looked "
                          u"up in the registry by concatenating the prefix "
                          u"with the option name, optionally preceded by "
                          u"the rule set name, to allow per-rule overrides."),
            value_type=schema.DottedName(),
            required=False,
        )
    

#
# Internal abstractions
# 

class IRulesetLookup(Interface):
    """Abstraction for the lookup of response rulesets from published objects.
    This is an unnamed multi- adapter from (published, request).
    
    The main reason for needing this is that some publishable resources cannot
    be adequately mapped to a rule set by context type alone. In particular,
    Zope page templates in skin layers or created through the web can only be
    distinguished by their name, and cache rules may vary depending on how
    they are acquired.
    
    We don't implement anything other than the default ``z3c.caching`` lookup
    in this package, and would expect the use of a custom ``IRulesetLookup``
    to be a last resort for integrators.
    """
    
    def __call__():
        """Get the ruleset for the adapted published object and request.
        
        Returns a ruleset name (a string) or None.
        """

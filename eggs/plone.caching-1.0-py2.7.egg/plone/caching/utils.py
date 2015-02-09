import types

from zope.component import queryUtility, getUtility
from zope.component import queryMultiAdapter

from plone.registry.interfaces import IRegistry

from plone.caching.interfaces import ICachingOperation
from plone.caching.interfaces import ICachingOperationType
from plone.caching.interfaces import IRulesetLookup
from plone.caching.interfaces import ICacheSettings

def lookupOptions(type_, rulename, default=None):
    """Look up all options for a given caching operation type, returning
    a dictionary. They keys of the dictionary will be the items in the
    ``options`` tuple of an ``ICachingOperationType``.
    
    ``type`` should either be a ``ICachingOperationType`` instance or the name
    of one.
    
    ``rulename`` is the name of the rule being executed.
    
    ``default`` is the default value to use for options that cannot be found.
    """
    
    if not ICachingOperationType.providedBy(type_):
        type_ = getUtility(ICachingOperationType, name=type_)
    
    options = {}
    registry = queryUtility(IRegistry)
    
    for option in getattr(type_, 'options', ()):
        options[option] = lookupOption(type_.prefix, rulename, option, default, registry)
    
    return options

def lookupOption(prefix, rulename, option, default=None, _registry=None):
    """Look up an option for a particular caching operation.
    
    The idea is that a caching operation may read configuration options from
    plone.registry according to the following rules:
    
    * If ${prefix}.${rulename}.${option} exists, get that
    * Otherwise, if ${prefix}.${option} exists, get that
    * Otherwise, return ``default``
    
    This allows an operation to have a default setting, as well as a per-rule
    override.
    """
    
    # Avoid looking this up multiple times if we are being called from lookupOptions
    registry = _registry
    
    if registry is None:
        registry = queryUtility(IRegistry)
    
    if registry is None:
        return default
    
    key = "%s.%s.%s" % (prefix, rulename, option,)
    if key in registry:
        return registry[key]
    
    key = "%s.%s" % (prefix, option,)
    if key in registry:
        return registry[key]
    
    return default

def findOperation(request):
    
    published = request.get('PUBLISHED', None)
    if published is None:
        return None, None, None
    
    # If we get a method, try to look up its class
    if isinstance(published, types.MethodType):
        published = getattr(published, 'im_self', published)
    
    registry = queryUtility(IRegistry)
    if registry is None:
        return None, None, None
    
    settings = registry.forInterface(ICacheSettings, check=False)
    if not settings.enabled:
        return None, None, None
    
    if settings.operationMapping is None:
        return None, None, None
    
    lookup = queryMultiAdapter((published, request,), IRulesetLookup)
    if lookup is None:
        return None, None, None
    
    # From this point, we want to at least log
    rule = lookup()
    
    if rule is None:
        return None, None, None
    
    operationName = settings.operationMapping.get(rule, None)
    if operationName is None:
        return rule, None, None
    
    operation = queryMultiAdapter((published, request), ICachingOperation, name=operationName)
    return rule, operationName, operation

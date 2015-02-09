""" Rulesets are registered for entities, which can be a type or an interface.
This means the lookup mechanism needs to be aware of all of those and deal
with things like derived classes as well. Luckily we have a framework which
already implements that: zope.component.

We will (ab)use the zope.component registries by registering a dummy adapter
for the entity to a special ICacheRule interface and which will always return
the ruleset id.
"""

import warnings

from zope.interface import implements, Interface, Attribute

from zope.component import adapts, queryUtility, getUtilitiesFor, getGlobalSiteManager
from zope.component.interfaces import IComponents

from z3c.caching.interfaces import IRulesetRegistry
from z3c.caching.interfaces import IRulesetType

class ICacheRule(Interface):
    """Represents the cache rule applied to an object.    
    This is strictly an implementation detail of IRulesetRegistry.
    """
    
    id = Attribute("The identifier of this cache rule")

class CacheRule(object):
    __slots__ = ("id")
    implements(ICacheRule)
    
    def __init__(self, identifier):
        self.id = identifier

class RulesetType(object):
    __slots__ = ('name', 'title', 'description',)
    implements(IRulesetType)
    
    def __init__(self, name, title, description):
        self.name = name
        self.title = title
        self.description = description

def get_context_to_cacherule_adapter_factory(rule):
    """Given a cache rule return an adapter factory which expects an object 
    but only returns the pre-specified cache rule."""
    def CacheRuleFactory(context):
        return CacheRule(rule)
    CacheRuleFactory.id = rule
    return CacheRuleFactory

class RulesetRegistry(object):

    implements(IRulesetRegistry)
    adapts(IComponents)

    def __init__(self, registry):
        self.registry = registry
        
    def register(self, obj, rule):
        rule = str(rule) # We only want ascii, tyvm
        
        if self.explicit and queryUtility(IRulesetType, rule) is None:
            raise LookupError("Explicit mode set and ruleset %s not found" % rule)
        
        factory = get_context_to_cacherule_adapter_factory(rule)
        existing = self.directLookup(obj)
        if existing is None:
            # Only register if we haven't got this one already
            self.registry.registerAdapter(factory, provided=ICacheRule, required=(obj,))
        else:
            warnings.warn("Ignoring attempted to register caching rule %s for %s.  %s is already registered." % (rule, `obj`, existing))
        return None


    def unregister(self, obj):
        self.registry.unregisterAdapter(provided=ICacheRule, required=(obj,))
        return None

    def clear(self):
        # We force the iterator to be evaluated to start with as the backing
        # storage will be changing size
        for rule in list(self.registry.registeredAdapters()):
            if rule.provided != ICacheRule:
                continue # Not our responsibility
            else:
                self.registry.unregisterAdapter(factory=rule.factory,
                                                provided=rule.provided, 
                                                required=rule.required)
        
        for type_ in list(self.registry.registeredUtilities()):
            if type_.provided != IRulesetType:
                continue # Not our responsibility
            else:
                self.registry.unregisterUtility(component=type_.component,
                                                provided=IRulesetType, 
                                                name=type_.name)
        
        self.explicit = False
        return None

    def lookup(self, obj):
        rule = ICacheRule(obj, None)
        if rule is not None:
            return rule.id
        return None
    
    __getitem__ = lookup
    
    def declareType(self, name, title, description):
        type_ = RulesetType(name, title, description)
        self.registry.registerUtility(type_, IRulesetType, name=name)
    
    def enumerateTypes(self):
        for name, type_ in getUtilitiesFor(IRulesetType):
            yield type_
    
    def _get_explicit(self):
        return getattr(self.registry, '_z3c_caching_explicit', False)
    def _set_explicit(self, value):
        setattr(self.registry, '_z3c_caching_explicit', value)
    explicit = property(_get_explicit, _set_explicit)
    
    # Helper methods
    
    def directLookup(self, obj):
        """Find a rule _directly_ assigned to `obj`"""
        for rule in self.registry.registeredAdapters():
            if rule.provided != ICacheRule:
                continue
            if rule.required == (obj, ):
                return rule.factory(None).id
        return None

def getGlobalRulesetRegistry():
    return IRulesetRegistry(getGlobalSiteManager(), None)

# Convenience API

def register(obj, rule):
    registry = getGlobalRulesetRegistry()
    if registry is None:
        raise LookupError("Global registry initialised")
    return registry.register(obj, rule)

def unregister(obj):
    registry = getGlobalRulesetRegistry()
    if registry is None:
        raise LookupError("Global registry initialised")
    return registry.unregister(obj)

def lookup(obj):
    registry = getGlobalRulesetRegistry()
    if registry is None:
        return None
    return registry.lookup(obj)

def enumerateTypes():
    registry = getGlobalRulesetRegistry()
    if registry is None:
        raise LookupError("Global registry initialised")
    return registry.enumerateTypes()

def declareType(name, title, description):
    registry = getGlobalRulesetRegistry()
    if registry is None:
        raise LookupError("Global registry initialised")
    registry.declareType(name, title, description)

def setExplicitMode(mode=True):
    registry = getGlobalRulesetRegistry()
    if registry is None:
        raise LookupError("Global registry initialised")
    registry.explicit = mode

__all__ = ['getGlobalRulesetRegistry', 'register', 'unregister', 'lookup',
           'enumerateTypes', 'declareType', 'setExplicitMode']

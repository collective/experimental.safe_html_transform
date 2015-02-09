import doctest
import unittest

import zope.component.testing

# Dummy behaviors for the directives.txt test
from zope.interface import Interface, implements
from zope.component import adapts
from zope import schema

# Simple adapter behavior - no context restrictions

class IAdapterBehavior(Interface):
    pass

class AdapterBehavior(object):
    implements(IAdapterBehavior)
    def __init__(self, context):
        self.context = context

# Adapter behavior with explicit context restriction

class IRestrictedAdapterBehavior(Interface):
    pass

class RestrictedAdapterBehavior(object):
    implements(IRestrictedAdapterBehavior)
    def __init__(self, context):
        self.context = context

class IMinimalContextRequirements(Interface):
    pass
    
# Behavior with interface and for_ implied by factory

class IImpliedRestrictionAdapterBehavior(Interface):
    pass

class ISomeContext(Interface):
    pass

class ImpliedRestrictionAdapterBehavior(object):
    implements(IImpliedRestrictionAdapterBehavior)
    adapts(ISomeContext)
    
    def __init__(self, context):
        self.context = context

# Behavior with marker

class IMarkerBehavior(Interface):
    pass

# For test of the annotation factory

class IAnnotationStored(Interface):
    some_field = schema.TextLine(title=u"Some field", default=u"default value")

# Behavior and marker

class IMarkerAndAdapterBehavior(Interface):
    pass

class IMarkerAndAdapterMarker(Interface):
    pass

def test_suite():
    return unittest.TestSuite((
        
        doctest.DocFileSuite('behaviors.txt',
            # setUp=setUp,
            tearDown=zope.component.testing.tearDown),

        doctest.DocFileSuite('directives.txt',
            setUp=zope.component.testing.setUp,
            tearDown=zope.component.testing.tearDown),

        doctest.DocFileSuite('annotation.txt',
            setUp=zope.component.testing.setUp,
            tearDown=zope.component.testing.tearDown),

        ))

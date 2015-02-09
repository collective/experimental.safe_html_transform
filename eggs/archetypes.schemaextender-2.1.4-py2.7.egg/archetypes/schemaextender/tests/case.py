import unittest
from zope.interface import implements
from zope.component import provideAdapter
from zope.component import getGlobalSiteManager
from archetypes.schemaextender.extender import instanceSchemaFactory
from archetypes.schemaextender.interfaces import IExtensible
from Products.Archetypes.public import BaseObject


class ExtensibleType(BaseObject):
    """A very simple extensible type."""
    implements(IExtensible)


class TestCase(unittest.TestCase):

    def setUp(self):
        self._adapters=[]
        self.provideAdapter(instanceSchemaFactory)
        self.instance=ExtensibleType("id")

    def tearDown(self):
        sm=getGlobalSiteManager()
        for (args, kwargs) in self._adapters:
            sm.unregisterAdapter(*args, **kwargs)

    def provideAdapter(self, *args, **kwargs):
        provideAdapter(*args, **kwargs)
        self._adapters.append((args, kwargs))

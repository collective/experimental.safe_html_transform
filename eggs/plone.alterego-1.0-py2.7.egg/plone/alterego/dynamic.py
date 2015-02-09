import sys
from new import module

from zope.interface import implements
from zope.component import queryUtility

from plone.alterego.interfaces import IDynamicModule
from plone.alterego.interfaces import IDynamicObjectFactory

class DynamicModule(module):
    """A module that can create objects on the fly.
    """
    
    implements(IDynamicModule)

    def __getattr__(self, name):
        
        if name == '__path__':
            raise AttributeError("Dynamic modules do not have __path__'s")
        
        factory = queryUtility(IDynamicObjectFactory, name=self.__name__)
        if factory is None:
            raise AttributeError("Cannot find dynamic object factory for module %s" % self.__name__)
        
        obj = factory(name, self)
        if obj is None:
            raise AttributeError("Dynamic module factory did not want to create %s in %s" % (name, self.__name__))

        return obj
            
def create(dotted_name):
    dynamic = DynamicModule(dotted_name)
    sys.modules[dotted_name] = dynamic
    return dynamic
    
__all__ = ('create',)
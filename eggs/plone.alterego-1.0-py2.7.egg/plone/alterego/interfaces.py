from zope.interface import Interface

class IDynamicModule(Interface):
    """Marker interface for dynamic modules
    """

class IDynamicObjectFactory(Interface):
    """A factory capable of creating objects on the fly.
    
    This should be registered as a named utility. The name is the name of
    the dynamic module. Thus, there is a one-to-one mapping between the 
    dynamic module as the the 
    """
    
    def __call__(name, module):
        """Create an object with the given name in the given (dynamic) module.
        
        This will only be called once for each name. __module__ is the module
        that the object will live in, and name is the name of the object 
        itself. That is,  the full dotted name of the generated object will be 
        "%s.%s" % (module.__name__, name).
        
        This function should return a new object, or return None, in which
        case the dynamic module will generate an AttributeError. There is
        no need to mess with sys.modules or modify the 'module' object.
        """
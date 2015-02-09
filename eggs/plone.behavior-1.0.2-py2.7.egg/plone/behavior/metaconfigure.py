from zope.interface import Interface

from zope import schema
from zope.configuration import fields as configuration_fields
from zope.configuration.exceptions import ConfigurationError

from zope.component.zcml import adapter
from zope.component.zcml import utility

from plone.behavior.interfaces import IBehavior
from plone.behavior.interfaces import ISchemaAwareFactory

from plone.behavior.registration import BehaviorRegistration
from plone.behavior.factory import BehaviorAdapterFactory

class IBehaviorDirective(Interface):
    """Directive which registers a new behavior type (a global, named
    utility) and associated behavior adapter factory (a global, unnamed
    adapter)
    """
    
    title = configuration_fields.MessageID(
        title=u"Title",
        description=u"A user friendly title for this behavior",
        required=True)
        
    description = configuration_fields.MessageID(
        title=u"Description",
        description=u"A longer description for this behavior",
        required=False)
                           
    provides = configuration_fields.GlobalInterface(
        title=u"An interface to which the behavior can be adapted",
        description=u"This is what the conditional adapter factory will be registered as providing",
        required=True)
    
    marker = configuration_fields.GlobalInterface(
        title=u"A marker interface to be applied by the behavior",
        description=u"If provides is given and factory is not given, then this is optional",
        required=False)
        
    factory = configuration_fields.GlobalObject(
        title=u"The factory for this behavior",
        description=u"If this is not given, the behavior is assumed to provide a marker interface",
        required=False)

    for_ = configuration_fields.GlobalObject(
        title=u"The type of object to register the conditional adapter factory for",
        description=u"This is optional - the default is to register the factory for zope.interface.Interface",
        required=False)
        
def behaviorDirective(_context, title, provides, description=None, marker=None, factory=None, for_=None):
    
    if marker is None and factory is None:
        marker = provides

    if factory is None and marker is not None and marker is not provides:
        raise ConfigurationError(u"You cannot specify a different 'marker' and 'provides' if there is no adapter factory for the provided interface.")

    # Instantiate the real factory if it's the schema-aware type. We do
    # this here so that the for_ interface may take this into account.
    if factory is not None and ISchemaAwareFactory.providedBy(factory):
        factory = factory(provides)
    
    # Attempt to guess the factory's adapted interface and use it as the for_
    if for_ is None and factory is not None:
        adapts = getattr(factory, '__component_adapts__', None)
        if adapts:
            if len(adapts) != 1:
                raise ConfigurationError(u"The factory cannot be declared a multi-adapter.")
            for_ = adapts[0]
        else:
            for_ = Interface
    elif for_ is None:
        for_ = Interface
    
    registration = BehaviorRegistration(title=title,
                                        description=description,
                                        interface=provides,
                                        marker=marker,
                                        factory=factory)

    adapter_factory = BehaviorAdapterFactory(registration)
    
    utility(_context, 
            provides=IBehavior,
            name=provides.__identifier__,
            component=registration)
    
    if factory is not None:
        adapter(_context, 
                factory=(adapter_factory,),
                provides=provides,
                for_=(for_,))

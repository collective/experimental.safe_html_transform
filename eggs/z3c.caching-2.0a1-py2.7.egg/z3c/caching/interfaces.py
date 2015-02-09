from zope.interface import Interface
from zope.component.interfaces import IObjectEvent
from zope import schema

class IRulesetRegistry(Interface):
    
    def register(obj, rule):
        """Mark objects that are implementers of `obj` to use the caching 
        rule `rule`. The name should be a dotted name, consisting only of
        upper or lowercase letters, digits, and/or periods.
        """
    
    def unregister(obj):
        """Remove any prior rule registration attached to obj in this 
        registry. N.B. registries are hierarchical, a parent may still 
        provide rules.
        """
    
    def clear():
        """Remove all rule registrations in this registry.
        """
    
    def lookup(obj):
        """Return the id of the rule associated with `obj`.  If no rule has 
        been registered `None` is returned.
        """
    
    def __getitem__(obj):
        """Convenience spelling for `lookup(obj)`.
        """
    
    def declareType(name, type, description):
        """Declare a new ruleset type. This will put a new `IRulesetType`
        into the list of objects returned by `enumerate`. The name should be
        a dotted name, consisting only of upper or lowercase letters, digits,
        and/or periods.
        """
    
    def enumerateTypes():
        """Return a sequence of all unique registered rule set types, as
        ``IRuleSetType`` objects.
        """
    
    explicit = schema.Bool(
            title=u"Explicit mode",
            description=u"If true, ruleset types must be declared before being used.",
            required=True,
            default=False
        )

class IRulesetType(Interface):
    """A ruleset type. The name can be used in a <cache:ruleset /> directive.
    The title and description are used for UI support.
    """
    
    name        = schema.DottedName(title=u"Ruleset name")
    title       = schema.TextLine(title=u"Title")
    description = schema.TextLine(title=u"Description", required=False)

class ILastModified(Interface):
    """An abstraction to help obtain a last-modified date for a published
    resource.
    
    Should be registered as an unnamed adapter from a published object
    (e.g. a view).
    """
    
    def __call__():
        """Return the last-modified date, as a Python datetime object.
        
        The datetime returned must be timezone aware and should normally be
        in the local timezone.
        
        May return None if the last modified date cannot be determined.
        """

class IPurgeEvent(IObjectEvent):
    """Event which can be fired to purge a particular object.
    
    This event is not fired anywhere in this package. Instead, higher level
    frameworks are expected to fire this event when an object may need to be
    purged.
    
    It is safe to fire the event multiple times for the same object. A given
    object will only be purged once.
    """

class IPurgeable(Interface):
    """Marker interface for content which should be purged when modified or
    removed.
    
    Event handlers are registered for ``IObjectModifiedEvent`` and
    ``IObjectRemovedEvent`` for contexts providing this interface. These are
    automatically purged.
    """

class IPurgePaths(Interface):
    """Return paths to send as PURGE requests for a given object.
    
    The purging hook will look up named adapters from the objects sent to
    the purge queue (usually by an IPurgeEvent being fired) to this interface.
    The name is not significant, but is used to allow multiple implementations
    whilst still permitting per-type overrides. The names should therefore
    normally be unique, prefixed with the dotted name of the package to which
    they belong.
    """
    
    def getRelativePaths():
        """Return a list of paths that should be purged. The paths should be
        relative to the virtual hosting root, i.e. they should start with a
        '/'.
        
        These paths will be rewritten to incorporate virtual hosting if
        necessary.
        """
        
    def getAbsolutePaths():
        """Return a list of paths that should be purged. The paths should be
        relative to the domain root, i.e. they should start with a '/'.
        
        These paths will *not* be rewritten to incorporate virtual hosting.
        """

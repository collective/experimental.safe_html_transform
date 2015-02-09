from zope.interface import Interface, Attribute, implements
from wicked.fieldevent.interfaces import ITxtFilter, IFieldEvent
from wicked.fieldevent.interfaces import IFieldStorageEvent
from zope.annotation.interfaces import IAnnotatable

class IUID(Interface):
    """an effectively unique identifier for the context of the system"""


class IWickedFilter(ITxtFilter):
    """
    Wicked txtfilter

    @@ fill out interface for subscription adapter
    """


class IAmWickedField(Interface):
    """
    A 'field' specifically designated for wicked behavior.  Could be
    just a wrapper for a getter and a setter combo.

    @@ will probably initially have some at cruft to it
    """


class IAmWicked(IAnnotatable):
    """
    wicked content... marker to indicate a piece of content has wicked
    fields
    """


class IWickedTarget(Interface):
    """
    marker interface for an object linked to in a wicked text area
    """


class IWickedBacklink(Interface):
    """
    Backlink marker

    @@ is this used?
    """


class IWickedFilter(Interface):
    """
    Wicked resolving filter
    """
    ### this need complete documentation and test to verify


class IBacklinkManager(Interface):
    """
    this might become the wicked storage manager...
    """
    def manageLinks():
        """
        removes old links adds new
        """

    def addLinks(links, scope, dups=[]):
        """
        retrieves brains, and sets backlinks for a colletion
        wicked links.  will filter against identifiers(UIDs)
        in dups (this allow chaining with removelinks, which
        returns duplicate links)
        """

    def getLinks():
        """
        returns all current backlinks
        """

    def set(brain, link):
        """
        creates a backlink(a smart pointer pointing for the links target)
        and caches link
        """

    def remove(brain):
        """
        does the actual backlink removal and cache unsetting
        """

    def removeLinks(exclude=tuple()):
        """
        iterates over a list of brain representing existing backlink
        and executes backlink deletion if not included in exclude

        @exclude: list of strings 'links' not to erase
        """

class IATBacklinkManager(IBacklinkManager):
    """
    A manager for Archetypes reference (aka smart pointer) based backlinka
    """
    relation = Attribute( """
    Name of Archetype relationship. Used to retrieve
    backlinks from reference engine
    """)


class ICacheManager(Interface):
    """
    a cache manager that cache per content instance
    on the content type itself. It manages a dual level data
    structure: dict(section=dict(key=value))
    """
    cache_attr = Attribute('attribute to access cache through')
    section = Attribute('attribute to access sub-cache through')
    cache=Attribute('Actually persisted cache object')

    def __init__(field, context):
        """
        cache manager multiadapts the field and the context
        """

    def get(key, default, **kwargs):
        """
        @rendered wicked link
        """

    def set(key, text):
        """
        sets text to cache
        """

    def unset(key):
        """
        invalidates cache key
        """

    def _get_store():
        """
        create and / or
        @return the  master store
        """

    def _get_cache():
        """
        @return actual datastructure
        for getting and setting
        """

class IWickedQuery(Interface):
    """
    object for handling and returning
    dataobjects for wicked prep
    for the macro parser
    """

    chunk = Attribute('unaltered string from inside ((wicked link))')
    normalized = Attribute('normalled chunk')
    scope = Attribute('scoping parameter for "scoped" searches')

    def scopedSearch(best_match):
        """
        @param best_match : attempt to make
        best match for query returned

        @return: list of dataobjects
        """

    def search(chunk, normalized, best_match):
        """
        @param best_match : attempt to make
        best match for query returned

        @return : list of dataobjects
        """

    def configure(chunk, normalized, scope):
        """
        configure set instance attributes

        @param chunk : instance attr
        @param normalized : instance attr
        @param scope : instance attr

        @return : None
        """

class IWickedLink(Interface):
    """renderer for wicked links"""

    def context():
        """
        context
        """

    def howmany():
        """
        @return integer
        how many links
        """

    def multiple():
        """
        @return boolean
        howmany > 1
        """

    def links():
        """
        @return list
        list of link datum
        """

    def singlelink():
        """
        @return boolean
        howmany == 1
        """

    def load(links, chunk, section):
        """
        load data for repeated rendering
        """


class IWickedEvent(Interface):
    """something wicked is happening"""


class IValueToString(Interface):
    """converts a field object to a raw string. mainly used to get
    around AT's un normalized value handling"""


class IScope(Interface):
    """a value used to determine breadth of resolver's search. usually a path"""


class WickedEvent(object):
    implements(IWickedEvent)

class IWickedContentAddedEvent(Interface):
    """a piece of content is add by wicked"""
    title = Attribute("title of new content")
    section = Attribute("subobject of concern")
    request = Attribute("current request")
    section = Attribute("field name inside context")
    context = Attribute("context linked from")
    newcontent = Attribute("object representing new content")

class WickedContentAddedEvent(WickedEvent):
    implements(IWickedContentAddedEvent)

    def __init__(self, context, newcontent, title, section, request=None):
        self.__dict__.update(locals())

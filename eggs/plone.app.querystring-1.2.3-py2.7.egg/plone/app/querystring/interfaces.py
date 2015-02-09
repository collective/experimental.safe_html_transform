from zope.interface import Interface
from zope.schema import Bool
from zope.schema import DottedName
from zope.schema import List
from zope.schema import Text
from zope.schema import TextLine


class IQuerystringRegistryReader(Interface):
    """Adapts a registry object to parse the querystring data
    """

    def __call__():
        """Return query string in dict-format.
        """


class IQueryOperation(Interface):
    title = TextLine(title=u"Title")
    description = Text(title=u"Description")
    operation = TextLine(title=u"Operation")
    widget = TextLine(title=u"Widget")


class IQueryField(Interface):
    title = TextLine(title=u"Title")
    description = Text(title=u"Description")
    enabled = Bool(title=u"Enabled")
    sortable = Bool(title=u"Sortable")
    operations = List(title=u"Operations",
                      value_type=DottedName(title=u"Operation ID"))
    vocabulary = TextLine(title=u"Vocabulary")
    group = TextLine(title=u"Group")


class IParsedQueryIndexModifier(Interface):
    """Transform a parsed query index in something different
    """

    def __call__(value):
        """
        Return a tuple with a new index name and a new value.
        if the index name returned is different from the native one, caller
        must replace treated index with the new ones.
        """

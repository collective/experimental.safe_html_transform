from Products.ATContentTypes.interfaces.interfaces import IATContentType
from zope.interface import Interface
try:
    from Products.CMFPlone.interfaces.syndication import ISyndicatable
except ImportError:
    from zope.interface import Interface as ISyndicatable


class IATTopic(IATContentType, ISyndicatable):
    """AT Topic marker interface
    """

    def listCriteriaTypes():
        """List available criteria types as dict
        """

    def listCriteriaMetaTypes():
        """List available criteria
        """

    def listSearchCriteriaTypes():
        """List available search criteria types as dict
        """

    def listSearchCriteriaMetaTypes():
        """List available search criteria
        """

    def listSortCriteriaTypes():
        """List available sort criteria types as dict
        """

    def listSortCriteriaMetaTypes():
        """List available sort criteria
        """

    def listCriteria():
        """Return a list of our criteria objects.
        """

    def listSearchCriteria():
        """Return a list of our search criteria objects.
        """

    def hasSortCriterion():
        """Tells if a sort criterai is already setup.
        """

    def getSortCriterion():
        """Return the Sort criterion if setup.
        """

    def removeSortCriterion():
        """remove the Sort criterion.
        """

    def setSortCriterion(field, reversed):
        """Set the Sort criterion.
        """

    def listAvailableFields():
        """Return a list of available fields for new criteria.
        """

    def listSortFields():
        """Return a list of available fields for sorting."""

    def listSubtopics():
        """Return a list of our subtopics.
        """

    def buildQuery():
        """Construct a catalog query using our criterion objects.
        """

    def queryCatalog(REQUEST=None, **kw):
        """Invoke the catalog using our criteria to augment any passed
            in query before calling the catalog.
        """

    def addCriterion(field, criterion_type):
        """Add a new search criterion.
        """

    def deleteCriterion(criterion_id):
        """Delete selected criterion.
        """

    def getCriterion(criterion_id):
        """Get the criterion object.
        """

    def addSubtopic(id):
        """Add a new subtopic.
        """


class IATTopicCriterion(Interface):
    """AT Topic Criterion interface
    """

    def widget(field_name, mode="view", field=None, **kwargs):
        """redefine widget() to allow seperate field_names from field
        """

    def getId():
        """get the objects id
        """

    def Type():
        """
        """

    def Description():
        """
        """

    def getCriteriaItems():
        """Return a sequence of items to be used to build the catalog query.
        """


class IATTopicSearchCriterion(IATTopicCriterion):
    """Interface for criteria used for searching
    """


class IATTopicSortCriterion(IATTopicCriterion):
    """Interface for criteria used for sorting
    """


class IATCTTopicsTool(Interface):
    """Mixin class for providing features to customize the display of topics
    """

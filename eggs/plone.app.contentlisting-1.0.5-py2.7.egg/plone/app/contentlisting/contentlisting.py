from plone.i18n.normalizer.interfaces import IIDNormalizer
from Products.CMFCore.utils import getToolByName
from zope.component import queryUtility
from zope import interface

from .interfaces import IContentListing, IContentListingObject


class ContentListing(object):
    """ An IContentListing implementation based on sequences of objects"""
    interface.implements(IContentListing)

    def __init__(self, sequence):
        self._basesequence = sequence

    def __getitem__(self, index):
        """`x.__getitem__(index)` <==> `x[index]`
        """
        return IContentListingObject(self._basesequence[index])

    def __len__(self):
        """ length of the resultset is equal to the length of the underlying
            sequence
        """
        return len(self._basesequence)

    @property
    def actual_result_count(self):
        bs = self._basesequence
        return getattr(bs, 'actual_result_count', len(bs))

    def __iter__(self):
        """ let the sequence be iterable and whenever we look at an object,
            it should be a ContentListingObject"""
        for obj in self._basesequence:
            yield IContentListingObject(obj)

    def __contains__(self, item):
        """`x.__contains__(item)` <==> `item in x`"""
        # It would be good if we could check this without waking all objects
        for i in self:
            if i == item:
                return True
        return False

    def __lt__(self, other):
        """`x.__lt__(other)` <==> `x < other`"""
        raise NotImplementedError

    def __le__(self, other):
        """`x.__le__(other)` <==> `x <= other`"""
        raise NotImplementedError

    def __eq__(self, other):
        """`x.__eq__(other)` <==> `x == other`"""
        raise NotImplementedError

    def __ne__(self, other):
        """`x.__ne__(other)` <==> `x != other`"""
        raise NotImplementedError

    def __gt__(self, other):
        """`x.__gt__(other)` <==> `x > other`"""
        raise NotImplementedError

    def __ge__(self, other):
        """`x.__ge__(other)` <==> `x >= other`"""
        raise NotImplementedError

    def __add__(self, other):
        """`x.__add__(other)` <==> `x + other`"""
        raise NotImplementedError

    def __mul__(self, n):
        """`x.__mul__(n)` <==> `x * n`"""
        raise NotImplementedError

    def __rmul__(self, n):
        """`x.__rmul__(n)` <==> `n * x`"""
        raise NotImplementedError

    def __getslice__(self, i, j):
        """`x.__getslice__(i, j)` <==> `x[i:j]`
        Use of negative indices is not supported.
        Deprecated since Python 2.0 but still a part of `UserList`.
        """
        return IContentListing(self._basesequence[i:j])


class BaseContentListingObject(object):
    """A baseclass for the different types of contentlistingobjects
        To avoid duplication of the stuff that is not implementation-specific
    """

    def __eq__(self, other):
        """For comparing two contentlistingobject"""
        other = IContentListingObject(other)
        return self.uuid() == other.uuid()

    def ContentTypeClass(self):
        """A normalised type name that identifies the object in listings.
        used for CSS styling"""
        return "contenttype-" + queryUtility(IIDNormalizer).normalize(
            self.PortalType())

    def ReviewStateClass(self):
        """A normalised review state string for CSS styling use in listings."""
        return "state-" + queryUtility(IIDNormalizer).normalize(
            self.review_state())

    def appendViewAction(self):
        """decide whether to produce a string /view to append to links
        in results listings"""
        try:
            ttool = getToolByName(self.getDataOrigin(), 'portal_properties')
            types = ttool.site_properties.typesUseViewActionInListings
        except AttributeError:
            return ''
        if self.portal_type in types:
            return "/view"
        return ''

    def isVisibleInNav(self):
        """true iff this item should be visible in navigation trees"""
        if hasattr(self,'exclude_from_nav') and (self.exclude_from_nav() if callable(self.exclude_from_nav) else self.exclude_from_nav):
            return False
        portal_properties = getToolByName(self.getDataOrigin(), 'portal_properties')
        navtree_properties = getattr(portal_properties, 'navtree_properties')
        if self.portal_type in list(navtree_properties.metaTypesNotToList): return False
        if self.id in list(navtree_properties.idsNotToList): return False
        return True

from Acquisition import aq_base
from Acquisition import aq_get
from plone.app.layout.icons.interfaces import IContentIcon
from plone.uuid.interfaces import IUUID
from Products.CMFCore.utils import getToolByName
from zope.component import queryMultiAdapter
from zope import interface

from .contentlisting import BaseContentListingObject
from .interfaces import IContentListingObject


class RealContentListingObject(BaseContentListingObject):
    """A content object representation wrapping a real content object"""

    interface.implements(IContentListingObject)

    def __init__(self, obj):
        self._realobject = obj
        self.request = aq_get(obj, 'REQUEST')

    def __repr__(self):
        return "<plone.app.contentlisting.realobject." + \
               "RealContentListingObject instance at %s>" % (
            self.getPath(), )

    __str__ = __repr__

    def __getattr__(self, name):
        """We'll override getattr so that we can defer name lookups to
        the real underlying objects without knowing the names of all
        attributes.
        """
        if name.startswith('_'):
            raise AttributeError(name)
        obj = self.getObject()
        if hasattr(aq_base(obj), name):
            return getattr(aq_base(obj), name)
        else:
            raise AttributeError(name)

    def getObject(self):
        return self._realobject

    def getDataOrigin(self):
        """The origin of the data for the object.

        Sometimes we just need to know if we are looking at a brain or
        the real object.
        """
        return self.getObject()

    # a base set of elements that are needed but not defined in dublin core
    def getPath(self):
        return '/'.join(self.getObject().getPhysicalPath())

    def getURL(self):
        return self.getObject().absolute_url()

    def uuid(self):
        # content objects might have UID and might not. Same thing for
        # their brain.
        uuid = IUUID(self.getObject(), None)
        if uuid is not None:
            return uuid
        return self.getPath()

    def getIcon(self):
        obj = self.getObject()
        return queryMultiAdapter(
            (obj, self.request, obj),
            interface=IContentIcon)()

    def review_state(self):
        obj = self.getObject()
        wftool = getToolByName(obj, "portal_workflow")
        return wftool.getInfoFor(obj, 'review_state')

    def Type(self):
        """Dublin Core element - Object type"""
        obj = self.getObject()
        typestool = getToolByName(obj, 'portal_types')
        ti = typestool.getTypeInfo(obj)
        if ti is not None:
            return ti.Title()
        return obj.meta_type

# Needed: A method Type() that returns the same as is cataloged as Type.
# Currently Type() returns different values depending on the data source being
# a brain or a real object. Probably needed. Support for all the attributes
# from the indexablemetadata wrappers.

    def PortalType(self):
        obj = self.getObject()
        return obj.portal_type

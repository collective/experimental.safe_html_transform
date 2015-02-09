from zope.interface import implements
from zope.event import notify
from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent
from AccessControl import ClassSecurityInfo
from OFS.interfaces import IOrderedContainer
from Products.Archetypes.atapi import BaseFolder
from Products.ATContentTypes.config import PROJECTNAME
from Products.ATContentTypes.content.base import registerATCT
from Products.ATContentTypes.content.base import ATCTOrderedFolder
from Products.ATContentTypes.interface import IATFolder
from Products.ATContentTypes.permission import permissions
from Products.ATContentTypes.content.schemata import ATContentTypeSchema
from Products.ATContentTypes.content.schemata import finalizeATCTSchema
from Products.ATContentTypes.lib.constraintypes import ConstrainTypesMixinSchema
from Products.CMFPlone.utils import _createObjectByType
from plone.folder.interfaces import IOrderable
from plone.app.folder.base import BaseBTreeFolder
from plone.app.folder.bbb import folder_implements


ATFolderSchema = ATContentTypeSchema.copy() + ConstrainTypesMixinSchema
finalizeATCTSchema(ATFolderSchema, folderish=True, moveDiscussion=False)


class UnorderedFolder(BaseFolder):
    """ sample unordered (old-style) folder for testing purposes """

    def SearchableText(self):
        return ''


class OrderableFolder(BaseBTreeFolder):
    """ sample ordered btree-based folder (needing the interface) """
    implements(IOrderable)


class NonBTreeFolder(ATCTOrderedFolder):
    """ an old-style folder much like `ATFolder` before Plone 4;  this is
        a reduced version of `ATContentTypes.content.folder.ATFolder` """
    implements(IATFolder, IOrderedContainer)

    __implements__ = folder_implements

    schema = ATFolderSchema
    portal_type = 'NonBTreeFolder'
    archetype_name = 'NonBTreeFolder'
    security = ClassSecurityInfo()

permissions['NonBTreeFolder'] = PROJECTNAME + ': ATFolder'
registerATCT(NonBTreeFolder, PROJECTNAME)


def addNonBTreeFolder(container, id, **kwargs):
    """ at-constructor copied from ClassGen.py """
    obj = NonBTreeFolder(id)
    notify(ObjectCreatedEvent(obj))
    container._setObject(id, obj)
    obj = container._getOb(id)
    obj.initializeArchetype(**kwargs)
    notify(ObjectModifiedEvent(obj))
    return obj


def create(ctype, container, id, *args, **kw):
    """ helper to create old-style folders as their regular type/factory has
        been replaced in plone 4 and isn't available anymore for testing """
    if ctype == 'Folder':
        obj = addNonBTreeFolder(container, id, *args, **kw)
        obj._setPortalTypeName(ctype)
        return obj
    else:
        return _createObjectByType(ctype, container, id, *args, **kw)

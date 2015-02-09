from zope.interface import implements
from zope.component import adapts

from plone.app.layout.nextprevious.interfaces import INextPreviousProvider
from Products.ATContentTypes.interfaces.folder import IATFolder

from plone.memoize.instance import memoize

from Acquisition import aq_base
from Products.CMFCore.utils import getToolByName


class ATFolderNextPrevious(object):
    """Let a folder act as a next/previous provider. This will be
    automatically found by the @@plone_nextprevious_view and viewlet.
    """

    implements(INextPreviousProvider)
    adapts(IATFolder)

    def __init__(self, context):
        self.context = context

        sp = getToolByName(self.context, 'portal_properties').site_properties
        self.view_action_types = sp.getProperty('typesUseViewActionInListings', ())

    def getNextItem(self, obj):
        relatives = self.itemRelatives(obj.getId())
        return relatives["next"]

    def getPreviousItem(self, obj):
        relatives = self.itemRelatives(obj.getId())
        return relatives["previous"]

    @property
    def enabled(self):
        return self.context.getNextPreviousEnabled()

    @memoize
    def itemRelatives(self, oid):
        """Get the relative next and previous items
        """
        folder = self.context
        catalog = getToolByName(self.context, 'portal_catalog')
        position = folder.getObjectPosition(oid)

        previous = None
        next = None

        # Get the previous item
        if position - 1 >= 0:
            prev_brain = catalog(self.buildNextPreviousQuery(position=position - 1,
                                                             range='max',
                                                             sort_order='reverse'))
            if prev_brain and len(prev_brain) > 0:
                previous = self.buildNextPreviousItem(prev_brain[0])

        # Get the next item
        counter = getattr(aq_base(folder), 'objectCount', None)
        if counter is not None:
            count = counter()
        else:
            count = len(folder)

        if (position + 1) < count:
            next_brain = catalog(self.buildNextPreviousQuery(position=position + 1,
                                                             range='min'))

            if next_brain and len(next_brain) > 0:
                next = self.buildNextPreviousItem(next_brain[0])

        nextPrevious = {
            'next': next,
            'previous': previous,
            }

        return nextPrevious

    def buildNextPreviousQuery(self, position, range, sort_order=None):
        sort_on = 'getObjPositionInParent'

        query = {}
        query['sort_on'] = sort_on
        query['sort_limit'] = 1
        query['path'] = dict(query='/'.join(self.context.getPhysicalPath()),
                             depth=1)

        # Query the position using a range
        if position == 0:
            query[sort_on] = 0
        else:
            query[sort_on] = dict(query=position, range=range)

        # Filters on content
        query['is_default_page'] = False
        query['is_folderish'] = False

        # Should I sort in any special way ?
        if sort_order:
            query['sort_order'] = sort_order

        return query

    def buildNextPreviousItem(self, brain):
        return {'id': brain.getId,
                'url': self.getViewUrl(brain),
                'title': brain.Title,
                'description': brain.Description,
                'portal_type': brain.portal_type,
                }

    def getViewUrl(self, brain):
        """create link and support contents that requires /view
        """
        item_url = brain.getURL()

        if brain.portal_type in self.view_action_types:
            item_url += '/view'

        return item_url

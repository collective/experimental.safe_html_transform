from Products.CMFCore.utils import getToolByName
from plone.app.folder.nogopip import GopipIndex
import pkg_resources


# monkey patch for Plone 3.x:
# if the `getObjPositionInParent` index doesn't exist or else was replaced
# by something else (e.g. like in Plone 4.x), there's no need to wake up
# all those objects and `reindexOnReorder` can be cut short...


def reindexOnReorder(self, parent):
    """ reindexing of "gopip" is probably no longer needed :) """
    catalog = getToolByName(self, 'portal_catalog')
    index = catalog.Indexes.get('getObjPositionInParent')
    if not isinstance(index, GopipIndex):
        return self.__nogopip_old_reindexOnReorder(parent)


def applyPatches():
    try:
        # Plone 4 or higher
        pkg_resources.get_distribution('plone.app.upgrade')
    except pkg_resources.DistributionNotFound:
        # Patch is only needed on Plone 3
        from Products.CMFPlone.PloneTool import PloneTool
        PloneTool.__nogopip_old_reindexOnReorder = PloneTool.reindexOnReorder
        PloneTool.reindexOnReorder = reindexOnReorder

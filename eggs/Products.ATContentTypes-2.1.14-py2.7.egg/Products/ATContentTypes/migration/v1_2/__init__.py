"""Migration functions for ATContentTypes 1.2. These are called during the
   usual CMFPlone migration.
"""
import logging
import transaction

from Acquisition import aq_base
from zope.component import getSiteManager

from Products.ATContentTypes.config import TOOLNAME
from Products.ATContentTypes.tool.atct import ATCTTool
from Products.ATContentTypes.interfaces import IATCTTool
from Products.CMFCore.utils import getToolByName

logger = logging.getLogger('plone.app.upgrade')


def upgradeATCTTool(portal):
    tool = getToolByName(portal, TOOLNAME, None)
    sm = getSiteManager(context=portal)
    if not hasattr(aq_base(tool), '_version'):
        # the tool already has been upgraded
        return
    # First we get all relevant old configuration and make sure we get
    # real copies of the various objects
    old_conf = {}
    old_conf['album_batch_size'] = int(getattr(tool, 'album_batch_size', 30))
    old_conf['album_image_scale'] = str(getattr(tool, 'album_image_scale', 'thumb'))
    old_conf['image_types'] = list(getattr(tool, 'image_types', ['Image', 'News Item']))
    old_conf['folder_types'] = list(getattr(tool, 'folder_types', ['Image']))
    old_conf['single_image_scale'] = str(getattr(tool, 'single_image_scale', 'preview'))
    old_conf['topic_indexes'] = tool.topic_indexes.copy()
    old_conf['topic_metadata'] = tool.topic_metadata.copy()
    old_conf['allowed_portal_types'] = tuple(tool.allowed_portal_types)

    # Remove the old tool completely
    del(tool)
    portal._delObject(TOOLNAME)
    sm.unregisterUtility(provided=IATCTTool)
    transaction.savepoint(optimistic=True)

    # Create new tool
    portal._setObject(TOOLNAME, ATCTTool())
    tool = portal.get(TOOLNAME)
    sm.registerUtility(aq_base(tool), IATCTTool)
    # And apply the configuration again
    tool._setPropValue('album_batch_size', old_conf['album_batch_size'])
    tool._setPropValue('album_image_scale', old_conf['album_image_scale'])
    tool._setPropValue('image_types', tuple(old_conf['image_types']))
    tool._setPropValue('folder_types', tuple(old_conf['folder_types']))
    tool._setPropValue('single_image_scale', old_conf['single_image_scale'])
    tool._setPropValue('allowed_portal_types', old_conf['allowed_portal_types'])

    # XXX Index and metadata should be updated instead of being reapplied
    tool._setPropValue('topic_indexes', old_conf['topic_indexes'])
    tool._setPropValue('topic_metadata', old_conf['topic_metadata'])

    transaction.savepoint(optimistic=True)

    logger.info('Upgraded the ATContentTypes tool.')

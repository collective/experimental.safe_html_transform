##########################################################
#
# Licensed under the terms of the GNU Public License
# (see docs/LICENSE.GPL)
#
# Copyright (c) 2005:
#   - The Open Planning Project (http://www.openplans.org/)
#   - Whit Morriss <whit at www.openplans.org>
#   - and contributors
#
##########################################################

from zope.container.interfaces import IObjectAddedEvent
from zope.container.interfaces import IObjectRemovedEvent

from Products.Archetypes.interfaces import ISchema

from wicked import config, utils
from wicked.interfaces import IAmWicked, IAmWickedField, IUID

# @@ these a very at specific

def at_handle_target_deletion(ref, event):
    """
    Invalidate any pointer before object deletion
    """
    target = ref.getTargetObject()
    for field in ISchema(target).fields():
        if IAmWickedField.providedBy(field):
            wicked = utils.getWicked(field, target)
            wicked.unlink(ref.sourceUID)
            break

def at_handle_target_moved(obj, event):
    """
    when a target of a link is moved, or renamed we need to notify any
    objects that may be caching pointers
    """
    #@@ add more tests
    if IObjectRemovedEvent.providedBy(event):
        return

    refs=obj.getRefs(relationship=config.BACKLINK_RELATIONSHIP)
    path = '/'.join(obj.getPhysicalPath())
    for target in refs:
        for field in ISchema(target).fields():
            if IAmWickedField.providedBy(field):
                wicked = utils.getWicked(field, target)
                uid = IUID(obj)
                data = dict(path=path,
                        icon=obj.getIcon(),
                        uid=uid)
                wicked.cache.reset(uid, [data])



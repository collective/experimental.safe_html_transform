##########################################################
#
# Licensed under the terms of the GNU Public License
# (see docs/LICENSE.GPL)
#
# Copyright (c) 2005:
#   - The Open Planning Project (http://www.openplans.org/)
#   - Whit Morriss <whit@kalistra.com>
#   - and contributors
#
##########################################################

"""
BackLink
~~~~~~~~

A type of reference that can be used/extended to provide smarter
inter-document linking. With the support of an editor this can be
quite useful.
"""
from Products.Archetypes.references import Reference
from wicked import config
from wicked.interfaces import IWickedBacklink
from zope.interface import implements

class Backlink(Reference):
    """
    A backlink is a reference set on an object when it is targetted
    by a resolved wicked-link
    """
    implements(IWickedBacklink)
    relationship = config.BACKLINK_RELATIONSHIP
    def __repr__(self):
        return "<Backlink sid:%s tid:%s rel:%s>" %(self.sourceUID, self.targetUID, self.relationship)

    def targetURL(self):
        """
        let's stick this in the catalog this to keep things light
        """
        target = self.getTargetObject()
        if target:
            return target.absolute_url()
        return '#'




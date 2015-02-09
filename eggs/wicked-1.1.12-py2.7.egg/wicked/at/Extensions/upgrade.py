from Products.CMFCore.utils import getToolByName
from Products.Five.utilities.marker import mark
from wicked.at import config
from wicked.interfaces import IWickedBacklink
from wicked.interfaces import IWickedTarget

def upgrade09(site):
    refcat = getToolByName(site, 'reference_catalog')
    refs = (brain.getObject() for brain in \
               refcat(relationship=config.BACKLINK_RELATIONSHIP))

    for ref in refs:
        if ref:
            obj=ref.getSourceObject()
            mark(obj, IWickedTarget)
            if not IWickedBacklink.providedBy(ref):
                print ref
                mark(ref, IWickedBacklink)

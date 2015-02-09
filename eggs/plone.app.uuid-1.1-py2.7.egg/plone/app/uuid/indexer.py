from plone.indexer import indexer

from plone.uuid.interfaces import IUUID
from plone.uuid.interfaces import IUUIDAware

@indexer(IUUIDAware)
def uuidIndexer(obj):
    return IUUID(obj, None)

from zope.site.hooks import getSite
from Products.CMFCore.utils import getToolByName

def uuidToPhysicalPath(uuid):
    """Given a UUID, attempt to return the absolute path of the underlying
    object. Will return None if the UUID can't be found.
    """
    
    brain = uuidToCatalogBrain(uuid)
    if brain is None:
        return None
    
    return brain.getPath()

def uuidToURL(uuid):
    """Given a UUID, attempt to return the absolute URL of the underlying
    object. Will return None if the UUID can't be found.
    """
    
    brain = uuidToCatalogBrain(uuid)
    if brain is None:
        return None
    
    return brain.getURL()

def uuidToObject(uuid):
    """Given a UUID, attempt to return a content object. Will return
    None if the UUID can't be found.
    """
    
    brain = uuidToCatalogBrain(uuid)
    if brain is None:
        return None
    
    return brain.getObject()

def uuidToCatalogBrain(uuid):
    """Given a UUID, attempt to return a catalog brain.
    """
    
    site = getSite()
    if site is None:
        return None
    
    catalog = getToolByName(site, 'portal_catalog', None)
    if catalog is None:
        return None
    
    result = catalog(UID=uuid)
    if len(result) != 1:
        return None
    
    return result[0]

from zope.component import getUtility
from zope.app.intid.interfaces import IIntIds as app_IIntIds
from zope.intid.interfaces import IIntIds
from five.intid.site import addUtility
from five.intid.intid import IntIds
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.interfaces import IContentish

try:
    import Products.LinguaPlone
    Products.LinguaPlone
    HAS_LINGUAPLONE = True
except:
    HAS_LINGUAPLONE = False


def register_all_content_for_intids(portal):
    """Registers all existing content with the intid utility.  This
    will not be fast."""
    cat = getToolByName(portal, 'portal_catalog', None)
    intids = getUtility(IIntIds)
    register = intids.register
    # Take advantage of paths stored in keyreferences in five.intid to optimize
    # registration
    registered_paths = dict(
        (ref.path, None) for ref in intids.ids
        if hasattr(ref, 'path'))
    # Count how many objects we register
    registered = 0
    existing = 0
    if cat is not None:
        query = {'object_provides': IContentish.__identifier__}
        if HAS_LINGUAPLONE:
            query['Language'] = 'all'
        content = cat(query)
        for brain in content:
            if brain.getPath() in registered_paths:
                existing += 1
                continue
            try:
                obj = brain.getObject()
                register(obj)
                registered += 1
            except (AttributeError, KeyError):
                pass
    return registered, existing


def add_intids(context):
    # We need to explicilty use the zope.intids interface and
    # the zope.app.intids one
    addUtility(context, IIntIds, IntIds, ofs_name='intids',
               findroot=False)
    addUtility(context, app_IIntIds, IntIds, ofs_name='intids',
               findroot=False)


def installIntIds(context):
    if context.readDataFile('install_intids.txt') is None:
        return
    portal = context.getSite()
    add_intids(portal)
    return "Added intid utility."


def registerContent(context):
    if context.readDataFile('intid_register_content.txt') is None:
        return
    portal = context.getSite()
    registered, existing = register_all_content_for_intids(portal)
    return ("Assigned intids to %s content objects, %s objects "
            "already had intids." % (registered, existing))

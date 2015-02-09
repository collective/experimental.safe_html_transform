from zope.component import getSiteManager
from zope.interface import Interface
from plone.portlets.interfaces import IPortletType
from plone.portlets.registration import PortletType
import binascii


def registerPortletType(site, title, description, addview, for_=[Interface]):
    """Register a new type of portlet.

    site should be the local site where the registration should be made. The
    title and description should be meaningful metadata about the portlet for
    the UI.

    The addview should be the name of an add view registered, and must be
    unique.
    """
    sm = getSiteManager(site)

    portlet = PortletType()
    portlet.title = title
    portlet.description = description
    portlet.addview = addview
    portlet.for_ = for_

    sm.registerUtility(component=portlet, provided=IPortletType, name=addview)


def unregisterPortletType(site, addview):
    """Unregister a portlet type.

    site is the local site where the registration was made. The addview
    should is used to uniquely identify the portlet.
    """

    sm = getSiteManager(site)
    sm.unregisterUtility(provided=IPortletType, name=addview)


def hashPortletInfo(info):
    """Creates a hash from the portlet information.

    This is a bidirectional function. The hash must only contain characters
    acceptable as part of a html id.

    info is the portlet info dictionary. Hash is put into info, and
    also returned.
    """
    concat_txt = '%(manager)s\n%(category)s\n%(key)s\n%(name)s' % info
    info['hash'] = binascii.b2a_hex(concat_txt)
    return info['hash']


def unhashPortletInfo(hash):
    """Creates the portlet info from the hash.

    Output is the info dictionary (containing only the
    hashed fields).
    """
    concat_txt = binascii.a2b_hex(hash)
    manager, category, key, name = concat_txt.splitlines()
    info = dict(manager=manager, category=category, key=key, name=name, hash=hash)
    return info

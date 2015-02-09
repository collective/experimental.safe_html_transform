from zope.component import queryUtility
from zope.component import getMultiAdapter
from StringIO import StringIO
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.portlets.interfaces import IPortletManager
from plone.app.openid.portlets.login import Assignment as LoginAssignment
from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.browser.info import PASInfoView


def hasOpenIdPlugin(portal):
    pas_info=PASInfoView(portal, None)
    return pas_info.hasOpenIDExtractor()


def createOpenIdPlugin(portal, out):
    print >>out, "Adding an OpenId plugin"
    acl=getToolByName(portal, "acl_users")
    acl.manage_addProduct["plone.openid"].addOpenIdPlugin(
            id="openid", title="OpenId authentication plugin")


def activatePlugin(portal, out, plugin):
    acl=getToolByName(portal, "acl_users")
    plugin=getattr(acl, plugin)
    interfaces=plugin.listInterfaces()

    activate=[]

    for info in acl.plugins.listPluginTypeInfo():
        interface=info["interface"]
        interface_name=info["id"]
        if plugin.testImplements(interface):
            activate.append(interface_name)
            print >>out, "Activating interface %s for plugin %s" % \
                    (interface_name, info["title"])

    plugin.manage_activateInterfaces(activate)


def addLoginPortlet(portal, out):
    leftColumn = queryUtility(IPortletManager, name=u'plone.leftcolumn', context=portal)
    if leftColumn is not None:
        left = getMultiAdapter((portal, leftColumn,), IPortletAssignmentMapping, context=portal)
        if u'openid-login' not in left:
            print >>out, "Adding OpenID login portlet to the left column"
            left[u'openid-login'] = LoginAssignment()


def importVarious(context):
    # Only run step if a flag file is present (e.g. not an extension profile)
    if context.readDataFile('openid-pas.txt') is None:
        return

    site = context.getSite()
    out = StringIO()
    if not hasOpenIdPlugin(site):
        createOpenIdPlugin(site, out)
        activatePlugin(site, out, "openid")

    addLoginPortlet(site, out)


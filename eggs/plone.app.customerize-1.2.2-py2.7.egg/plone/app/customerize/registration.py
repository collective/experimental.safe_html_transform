from Products.Five.browser import BrowserView
from five.customerize.interfaces import IViewTemplateContainer, ITTWViewTemplate
from five.customerize.browser import mangleAbsoluteFilename
from five.customerize.zpt import TTWViewTemplate
from five.customerize.utils import findViewletTemplate
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.component import getGlobalSiteManager, getUtility
from zope.component import getAllUtilitiesRegisteredFor
from zope.viewlet.interfaces import IViewlet
from plone.portlets.interfaces import IPortletRenderer
from plone.browserlayer.interfaces import ILocalBrowserLayerType
from os.path import basename


def getViews(type):
    """ get all view registrations (stolen from zope.app.apidoc.presentation),
        both global and those registered for a specific layer """

    # A zope 3 view is any multi-adapter whose second requirement is a browser request,
    # or derivation thereof.  We also do an explicit check for interfaces that have
    # been registered as plone.browserlayer browser layers, because often these
    # do not extend IBrowserRequest even though they should.
    layers = getAllUtilitiesRegisteredFor(ILocalBrowserLayerType)
    gsm = getGlobalSiteManager()
    for reg in gsm.registeredAdapters():
        if (len(reg.required) > 1 and
                reg.required[1] is not None and
               (reg.required[1].isOrExtends(type) or
                reg.required[1] in layers)):
            yield reg

def interfaceName(iface):
    """ return a sensible name for the given interface """
    name = getattr(iface, '__name__', repr(iface))
    return getattr(iface, '__identifier__', name)

def templateViewRegistrations():
    regs = []
    for reg in getViews(IBrowserRequest):
        factory = reg.factory
        while hasattr(factory, 'factory'):
            factory = factory.factory
        # TODO: this should really be dealt with using
        # a marker interface on the view factory
        name = getattr(factory, '__name__', '')
        if name.startswith('SimpleViewClass') or \
                name.startswith('SimpleViewletClass') or \
                name.endswith('Viewlet') or \
                IViewlet.implementedBy(factory) or \
                IPortletRenderer.implementedBy(factory):
            attr, pt = findViewletTemplate(factory)
            if pt:
                reg.ptname = basename(pt.filename)
            else:
                reg.ptname = None
            regs.append(reg)
    return regs

def templateViewRegistrationInfos(regs, mangle=True):
    for reg in regs:
        if ITTWViewTemplate.providedBy(reg.factory):
            zptfile = None
            zcmlfile = None
            name = reg.name or reg.factory.name
            customized = reg.factory.getId()    # TODO: can we get an absolute url?
        else:
            attr, pt = findViewletTemplate(reg.factory)
            if attr is None:        # skip, if the factory has no template...
                continue
            zptfile = pt.filename
            zcmlfile = getattr(reg.info, 'file', None)

            if mangle:
                zptfile = mangleAbsoluteFilename(zptfile)
                zcmlfile = zcmlfile and mangleAbsoluteFilename(zcmlfile)

            name = reg.name or basename(zptfile)
            customized = None
        required = [interfaceName(r) for r in reg.required]
        required_str = ','.join(required)
        customize_url = '@@customizezpt.html?required=%s&view_name=%s' % (
                required_str,
                name)
        yield {
            'viewname': name,
            'required': required_str,
            'for': required[0],
            'type': required[1],
            'zptfile': zptfile,
            'zcmlfile': zcmlfile or 'n.a.',
            'customized': customized,
            'customize_url': customize_url,
        }

def templateViewRegistrationGroups(regs, mangle=True):
    ifaces = {}
    comp = lambda a,b: cmp(a['viewname'], b['viewname'])
    for reg in sorted(templateViewRegistrationInfos(regs, mangle=mangle), cmp=comp):
        key = reg['for']
        if ifaces.has_key(key):
            ifaces[key]['views'].append(reg)
        else:
            ifaces[key] = { 'name': key, 'views': [reg] }
    return sorted(ifaces.values(), cmp=lambda a,b: cmp(a['name'], b['name']))

def findTemplateViewRegistration(required, viewname):
    required = required.split(',')
    for reg in templateViewRegistrations():
        if required == [interfaceName(r) for r in reg.required]:
            if reg.name == viewname or reg.provided.isOrExtends(IPortletRenderer):
                return reg

def generateIdFromRegistration(reg):
    return '%s-%s' % (
        interfaceName(reg.required[0]).lower(),
        reg.name or reg.ptname
    )

def getViewClassFromRegistration(reg):
    # The view class is generally auto-generated, we usually want
    # the first base class, though if the view only has one base
    # (generally object or BrowserView) we return the full class
    # and hope that it can be pickled
    if IPortletRenderer.implementedBy(reg.factory):
        return reg.factory
    klass = reg.factory
    base = klass.__bases__[0]
    if base is BrowserView or base is object:
        return klass
    return base

def getTemplateCodeFromRegistration(reg):
    attr, template = findViewletTemplate(reg.factory)
    # TODO: we can't do template.read() here because of a bug in
    # Zope 3's ZPT implementation.
    return open(template.filename, 'rb').read()

def getViewPermissionFromRegistration(reg):
    permissions = getattr(reg.factory, '__ac_permissions__', [])
    for permission, methods in permissions:
        if methods[0] in ('', '__call__'):
            return permission

def createTTWViewTemplate(reg):
    attr, pt = findViewletTemplate(reg.factory)
    if pt:
        ptname = basename(pt.filename)
    else:
        ptname = None
    viewzpt = TTWViewTemplate(
        id = str(generateIdFromRegistration(reg)),
        text = getTemplateCodeFromRegistration(reg),
        view = getViewClassFromRegistration(reg),
        permission = getViewPermissionFromRegistration(reg),
        name = ptname)
    # conserve view name (at least for KSS kssattr-viewname to work
    viewzpt.manage_addProperty('view_name', reg.name, 'string') 
    return viewzpt

def customizeTemplate(reg):
    viewzpt = createTTWViewTemplate(reg)
    container = getUtility(IViewTemplateContainer)
    return container.addTemplate(viewzpt.getId(), viewzpt)


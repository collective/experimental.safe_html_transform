from Products.Five.browser import BrowserView
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.component import getSiteManager, getAllUtilitiesRegisteredFor
from plone.browserlayer.interfaces import ILocalBrowserLayerType
from Acquisition import aq_inner

from plone.app.customerize import registration
from five.customerize.interfaces import ITTWViewTemplate


class RegistrationsView(BrowserView):

    def getTemplateViewRegistrations(self, mangle=True):
        """ get all global view registrations and cycle through the local
            ones to see which views have already been customized ttw """
        regs = []
        local = {}
        for reg in self.getLocalRegistrations():
            local[(reg.required, str(reg.name), str(reg.factory.name))] = reg
        for reg in registration.templateViewRegistrations():
            lreg = local.get((reg.required, str(reg.name), str(reg.ptname)), None)
            if lreg is not None:
                regs.append(lreg)
            else:
                regs.append(reg)
        return registration.templateViewRegistrationGroups(regs, mangle=mangle)

    def getTemplateCodeFromRegistration(self):
        reg = self.getRegistrationFromRequest()
        return registration.getTemplateCodeFromRegistration(reg)

    def getTemplateViewRegistrationInfo(self):
        reg = self.getRegistrationFromRequest()
        return list(registration.templateViewRegistrationInfos([reg]))[0]

    def getRegistrationFromRequest(self):
        form = self.request.form
        return registration.findTemplateViewRegistration(form['required'],
            form['view_name'])

    def registerTTWView(self, viewzpt, reg):
        sm = getSiteManager(self.context)
        sm.registerAdapter(viewzpt, required = reg.required,
                           provided = reg.provided, name = reg.name)

    def customizeTemplate(self):
        reg = self.getRegistrationFromRequest()
        viewzpt = registration.customizeTemplate(reg)
        self.registerTTWView(viewzpt, reg)
        path = aq_inner(viewzpt).getPhysicalPath()
        url = self.request.physicalPathToURL(path) + "/manage_workspace"
        self.request.response.redirect(url)

    def getLocalRegistrations(self):
        layers = getAllUtilitiesRegisteredFor(ILocalBrowserLayerType)
        components = getSiteManager(self.context)
        for reg in components.registeredAdapters():
            if (len(reg.required) in (2, 4, 5) and
                   (reg.required[1].isOrExtends(IBrowserRequest) or
                    reg.required[1] in layers) and
                    ITTWViewTemplate.providedBy(reg.factory)):
                yield reg


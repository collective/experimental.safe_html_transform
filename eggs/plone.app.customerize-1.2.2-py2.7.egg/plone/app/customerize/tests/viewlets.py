from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.layout.viewlets.common import ViewletBase


class StandardViewlet(ViewletBase):
    """ a viewlet class for testing purposes """

    render = ViewPageTemplateFile('standard.pt')


class LayerViewlet(ViewletBase):
    """ a viewlet class for testing purposes """

    render = ViewPageTemplateFile('local.pt')



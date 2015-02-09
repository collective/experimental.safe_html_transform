from plone.app.layout.viewlets.common import ViewletBase


class Resources(ViewletBase):

    def render(self):
        return u"""
      """ % {'portal_url': self.site_url}
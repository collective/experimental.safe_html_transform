from Acquisition import aq_inner
from Products.Five.browser import BrowserView

from plone.app.textfield.interfaces import ITransformer


class Transform(BrowserView):
    """Invoke a transformation on a RichText field.

    Invoke as:

        context/@@text-transform/fieldname

    Or:

        context/@@text-transform/fieldname/major/minor

    e.g.

        context/@@text-transform/fieldname/text/plain
    """

    fieldName = None
    major = None
    minor = None

    def __getitem__(self, name):
        if self.fieldName is None:
            self.fieldName = name
        elif self.major is None:
            self.major = name
        elif self.minor is None:
            self.minor = name
        return self

    def __call__(self, value=None, fieldName=None, mimeType=None):
        context = aq_inner(self.context)

        if fieldName is None:
            fieldName = self.fieldName

        if value is None:
            value = getattr(context, fieldName)

        if mimeType is None:
            if not self.major or not self.minor:
                mimeType = value.outputMimeType
            else:
                mimeType = "%s/%s" % (self.major, self.minor, )

        transformer = ITransformer(context)
        return transformer(value, mimeType)

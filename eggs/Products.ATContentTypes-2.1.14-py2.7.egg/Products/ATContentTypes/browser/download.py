from zope.interface import implements
from zope.publisher.interfaces import IPublishTraverse
from zope.publisher.interfaces import NotFound as pNotFound
from AccessControl import Unauthorized
from Products.Five import BrowserView


class DownloadArchetypeFile(BrowserView):
    """Basically, straight copy from plone.namedfile
    """
    implements(IPublishTraverse)

    def __init__(self, context, request):
        super(DownloadArchetypeFile, self).__init__(context, request)
        self.fieldname = None
        self.filename = None

    def publishTraverse(self, request, name):

        if self.fieldname is None:  # ../@@download/fieldname
            self.fieldname = name
        elif self.filename is None:  # ../@@download/fieldname/filename
            self.filename = name
        else:
            raise pNotFound(self, name, request)

        return self

    def __call__(self):
        file = self._getFile()
        return file.index_html(disposition='attachment')

    def _getFile(self):
        context = getattr(self.context, 'aq_explicit', self.context)
        field = context.getField(self.fieldname)

        if field is None:
            raise pNotFound(self, self.fieldname, self.request)
        if not field.checkPermission('r', context):
            raise Unauthorized()
        return field.get(context)

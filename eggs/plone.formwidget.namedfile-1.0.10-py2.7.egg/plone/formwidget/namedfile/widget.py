try:
    from  os import SEEK_END
except ImportError:
    from posixfile import SEEK_END
import urllib

from Acquisition import Explicit, aq_inner
from ZPublisher.HTTPRequest import FileUpload
from zope.component.hooks import getSite
from zope.component import adapter, getMultiAdapter
from zope.interface import implementer, implements, implementsOnly
from zope.size import byteDisplay
from zope.publisher.interfaces import IPublishTraverse, NotFound

from z3c.form.interfaces import IFieldWidget, IFormLayer, IDataManager, NOVALUE
from z3c.form.widget import FieldWidget
from z3c.form.browser import file

from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.MimetypesRegistry.common import MimeTypeException
from plone.namedfile.interfaces import INamedFileField, INamedImageField, INamed, INamedImage
from plone.namedfile.utils import safe_basename, set_headers, stream_data

from plone.formwidget.namedfile.interfaces import INamedFileWidget, INamedImageWidget


class NamedFileWidget(Explicit, file.FileWidget):
    """A widget for a named file object
    """
    implementsOnly(INamedFileWidget)

    klass = u'named-file-widget'
    value = None # don't default to a string

    @property
    def allow_nochange(self):
        return not self.ignoreContext and \
                   self.field is not None and \
                   self.value is not None and \
                   self.value != self.field.missing_value

    @property
    def filename(self):
        if self.field is not None and self.value == self.field.missing_value:
            return None
        elif INamed.providedBy(self.value):
            return self.value.filename
        elif isinstance(self.value, FileUpload):
            return safe_basename(self.value.filename)
        else:
            return None

    @property
    def file_size(self):
        if INamed.providedBy(self.value):
            return byteDisplay(self.value.getSize())
        else:
            return "0 KB"

    @property
    def _mimetype(self):
        registry = getToolByName(self.context, 'mimetypes_registry', None)
        if not registry:
            return None
        try:
            content_type = self.value.contentType
            mimetypes = registry.lookup(content_type)
        except AttributeError:
            mimetypes = [registry.lookupExtension(self.filename)]
        except MimeTypeException:
            return None

        if len(mimetypes):
            return mimetypes[0]
        else:
            return None

    @property
    def file_content_type(self):
        if not self.value:
            return ""

        mimetype = self._mimetype
        if mimetype:
            return mimetype.name()
        else:
            return getattr(self.value, 'contentType', None)

    @property
    def file_icon(self):
        if not self.value:
            return None

        mimetype = self._mimetype
        if mimetype and mimetype.icon_path:
            return "%s/%s" % (getToolByName(getSite(), 'portal_url')(),
                              mimetype.icon_path)
        else:
            return None


    @property
    def filename_encoded(self):
        filename = self.filename
        if filename is None:
            return None
        else:
            if isinstance(filename, unicode):
                filename = filename.encode('utf-8')
            return urllib.quote_plus(filename)

    @property
    def download_url(self):
        if self.field is None:
            return None
        if self.ignoreContext:
            return None
        if self.filename_encoded:
            return "%s/++widget++%s/@@download/%s" % (self.request.getURL(), self.name, self.filename_encoded)
        else:
            return "%s/++widget++%s/@@download" % (self.request.getURL(), self.name)

    def action(self):
        action = self.request.get("%s.action" % self.name, "nochange")
        if hasattr(self.form, 'successMessage') and self.form.status == self.form.successMessage:
            # if form action completed successfully, we want nochange
            action = 'nochange'
        return action

    def extract(self, default=NOVALUE):
        action = self.request.get("%s.action" % self.name, None)
        if self.request.get('PATH_INFO', '').endswith('kss_z3cform_inline_validation'):
            action = 'nochange'

        if action == 'remove':
            return None
        elif action == 'nochange':
            if self.ignoreContext:
                return default
            dm = getMultiAdapter((self.context, self.field,), IDataManager)
            # For sub-widgets to function use a query() not get()
            return dm.query(default)

        # empty unnamed FileUploads should not count as a value
        value = super(NamedFileWidget, self).extract(default)
        if isinstance(value, FileUpload):
            value.seek(0, SEEK_END)
            empty = value.tell()==0
            value.seek(0)
            if empty and not value.filename:
                return default
            value.seek(0)
        return value

class NamedImageWidget(NamedFileWidget):
    """A widget for a named file object
    """
    implementsOnly(INamedImageWidget)

    klass = u'named-image-widget'

    @property
    def width(self):
        if INamedImage.providedBy(self.value):
            return self.value._width
        else:
            return None

    @property
    def height(self):
        if INamedImage.providedBy(self.value):
            return self.value._height
        else:
            return None

    @property
    def thumb_width(self):
        width = self.width
        if not width:
            return 128
        else:
            return min(width, 128)

    @property
    def thumb_height(self):
        height = self.height
        if not height:
            return 128
        else:
            return min(height, 128)

    @property
    def alt(self):
        return self.title

class Download(BrowserView):
    """Download a file, via ../context/form/++widget++/@@download/filename
    """

    implements(IPublishTraverse)

    def __init__(self, context, request):
        super(BrowserView, self).__init__(context, request)
        self.filename = None

    def publishTraverse(self, request, name):

        if self.filename is None: # ../@@download/filename
            self.filename = name
        else:
            raise NotFound(self, name, request)

        return self

    def __call__(self):

        # TODO: Security check on form view/widget

        if self.context.ignoreContext:
            raise NotFound("Cannot get the data file from a widget with no context")

        if self.context.form is not None:
            content = aq_inner(self.context.form.getContent())
        else:
            content = aq_inner(self.context.context)
        field = aq_inner(self.context.field)

        dm = getMultiAdapter((content, field,), IDataManager)
        file_ = dm.get()
        if file_ is None:
            raise NotFound(self, self.filename, self.request)

        if not self.filename:
            self.filename = getattr(file_, 'filename', None)

        set_headers(file_, self.request.response, filename=self.filename)
        return stream_data(file_)

@implementer(IFieldWidget)
@adapter(INamedFileField, IFormLayer)
def NamedFileFieldWidget(field, request):
    return FieldWidget(field, NamedFileWidget(request))

@implementer(IFieldWidget)
@adapter(INamedImageField, IFormLayer)
def NamedImageFieldWidget(field, request):
    return FieldWidget(field, NamedImageWidget(request))

import cgi
import zope.publisher.browser
import ZPublisher.HTTPRequest

import z3c.form.interfaces
import z3c.form.converter

class FileUploadDataConverter(z3c.form.converter.FileUploadDataConverter):
    """Although ZPublisher's and zope.publisher's FileUpload
    implementations are almost identical, ``FileUploadDataConverter``
    makes an ``isinstance`` call that breaks duck-typing.

    Therefore, we override the stock ``FileUploadDataConverter`` with
    this little class that will do the right thing when a Zope 2
    FileUpload object is received.
    """
    def toFieldValue(self, value):
        """See interfaces.IDataConverter"""
        if isinstance(value, ZPublisher.HTTPRequest.FileUpload):
            fieldstorage = cgi.FieldStorage()
            fieldstorage.file = value
            fieldstorage.headers = value.headers
            fieldstorage.filename = value.filename
            value = zope.publisher.browser.FileUpload(fieldstorage)

        return super(FileUploadDataConverter, self).toFieldValue(value)

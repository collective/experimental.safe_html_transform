from zope.component import adapts

from z3c.form.converter import BaseDataConverter

from plone.namedfile.interfaces import INamedField, INamed
from plone.namedfile.utils import safe_basename

from plone.formwidget.namedfile.interfaces import INamedFileWidget

from ZPublisher.HTTPRequest import FileUpload

class NamedDataConverter(BaseDataConverter):
    """Converts from a file-upload to a NamedFile variant.
    """
    adapts(INamedField, INamedFileWidget)

    def toWidgetValue(self, value):
        return value

    def toFieldValue(self, value):
        
        if value is None or value == '':
            return self.field.missing_value

        if INamed.providedBy(value):
            return value
        elif isinstance(value, FileUpload):
            
            headers = value.headers
            filename = safe_basename(value.filename)
            
            if filename is not None and not isinstance(filename, unicode):
                # Work-around for
                # https://bugs.launchpad.net/zope2/+bug/499696
                filename = filename.decode('utf-8')
            
            contentType = 'application/octet-stream'
            if headers:
                contentType = headers.get('Content-Type', contentType)
            
            value.seek(0)
            data = value.read()
            if data or filename:
                return self.field._type(data=data, contentType=contentType, filename=filename)
            else:
                return self.field.missing_value
        
        else:
            return self.field._type(data=str(value))
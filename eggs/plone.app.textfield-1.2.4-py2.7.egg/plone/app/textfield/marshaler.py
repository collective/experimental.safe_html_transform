try:
    from plone.rfc822.defaultfields import BaseFieldMarshaler
    HAVE_MARSHALER = True
except ImportError:
    HAVE_MARSHALER = False

if HAVE_MARSHALER:

    from zope.interface import Interface
    from zope.component import adapts

    from plone.app.textfield.interfaces import IRichText
    from plone.app.textfield.value import RichTextValue


    class RichTextFieldMarshaler(BaseFieldMarshaler):
        """Field marshaler for plone.app.textfield values.
        """

        adapts(Interface, IRichText)

        ascii = False

        def encode(self, value, charset='utf-8', primary=False):
            if value is None:
                return
            return value.raw.encode(charset)

        def decode(self, value, message=None, charset='utf-8', contentType=None, primary=False):
            return RichTextValue(
                    raw=value,
                    mimeType=contentType or self.field.default_mime_type,
                    outputMimeType=self.field.output_mime_type,
                    encoding=charset
                )

        def getContentType(self):
            value = self._query()
            if value is None:
                return None
            return value.mimeType

        def getCharset(self, default='utf-8'):
            value = self._query()
            if value is None:
                return None
            return value.encoding

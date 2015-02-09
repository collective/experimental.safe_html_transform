plone.rfc822 marshaler
======================

This package includes a field marshaler for ``plone.rfc822``, which will be
installed if that package is installed.

To test this, we must first load some configuration:

    >>> configuration = """\
    ... <configure
    ...      xmlns="http://namespaces.zope.org/zope"
    ...      i18n_domain="plone.app.textfield.tests">
    ...
    ...     <include package="zope.component" file="meta.zcml" />
    ...     <include package="plone.rfc822" />
    ...     <include package="plone.app.textfield" file="marshaler.zcml" />
    ...
    ... </configure>
    ... """

    >>> from StringIO import StringIO
    >>> from zope.configuration import xmlconfig
    >>> xmlconfig.xmlconfig(StringIO(configuration))

Next, we will create a simple schema with which to test the marshaler

    >>> from zope.interface import Interface
    >>> from plone.app.textfield import RichText

    >>> class ITestContent(Interface):
    ...     _text = RichText(title=u"Rich text",
    ...                     output_mime_type='text/html',
    ...                     default_mime_type='text/plain')

We'll create an instance with some data, too. To avoid having to set up a
transformation utility, we'll simply provide the output value directly.

    >>> from plone.app.textfield.value import RichTextValue
    >>> from zope.interface import implements
    >>> class TestContent(object):
    ...     implements(ITestContent)
    ...     _text = RichTextValue(u"Some \xd8 plain text", 'text/plain', 'text/html', 'utf-8', u'<p>Some \xd8 plain text</p>')

    >>> t = TestContent()

We can now look up and test the marshaler:

    >>> from zope.component import getMultiAdapter
    >>> from plone.rfc822.interfaces import IFieldMarshaler

    >>> marshaler = getMultiAdapter((t, ITestContent['_text']), IFieldMarshaler)
    >>> marshaler.marshal()
    'Some \xc3\x98 plain text'
    >>> decoded = marshaler.decode('Some \xc3\x98 plain text', charset='utf-8', contentType='text/plain')
    >>> decoded.raw
    'Some \xc3\x98 plain text'
    >>> decoded.mimeType
    'text/plain'
    >>> decoded.outputMimeType
    'text/html'
    >>> decoded.encoding
    'utf-8'
    >>> marshaler.getContentType()
    'text/plain'
    >>> marshaler.getCharset('utf-8')
    'utf-8'
    >>> marshaler.ascii
    False

If we omit the content type (e.g. this is a non-primary field), the field's
default type is used.

    >>> decoded = marshaler.decode('Some \xc3\x98 plain text')
    >>> decoded.raw
    'Some \xc3\x98 plain text'
    >>> decoded.mimeType
    'text/plain'
    >>> decoded.outputMimeType
    'text/html'
    >>> decoded.encoding
    'utf-8'

Let's see how this looks in a message. We will mark the text field as a
primary field so that it is encoded in the content body.

    >>> from plone.rfc822.interfaces import IPrimaryField
    >>> from plone.rfc822 import constructMessageFromSchema
    >>> from plone.rfc822 import renderMessage

    >>> from zope.interface import alsoProvides
    >>> alsoProvides(ITestContent['_text'], IPrimaryField)

    >>> message = constructMessageFromSchema(t, ITestContent)
    >>> messageBody = renderMessage(message)
    >>> print messageBody
    MIME-Version: 1.0
    Content-Type: text/plain; charset="utf-8"
    <BLANKLINE>
    Some Ø plain text

Let's now use this message to construct a new object.

    >>> from email import message_from_string
    >>> inputMessage = message_from_string(messageBody)

    >>> newContent = TestContent()

    >>> from plone.rfc822 import initializeObjectFromSchema
    >>> initializeObjectFromSchema(newContent, ITestContent, inputMessage)
    >>> newContent._text.raw
    'Some \xc3\x98 plain text'
    >>> newContent._text.mimeType
    'text/plain'
    >>> newContent._text.outputMimeType
    'text/html'
    >>> newContent._text.encoding
    'utf-8'

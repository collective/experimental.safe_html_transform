Rich text field and value
=========================

The main purpose of this package is to provide a rich text field, which stores
rich text with an associated MIME type, with the possibility of transforming
the value to another MIME type.

The storage is optimised for the case where the transformed output value is
used frequently when the content object it resides on is used, whereas the
raw value is used only infrequently (e.g. when the object is modified).

Using the field
---------------

The field can be used much like any other field:

    >>> from zope.interface import Interface, implements
    >>> from plone.app.textfield import RichText

    >>> class IContent(Interface):
    ...     rich = RichText(title=u"Rich text")
    >>> field = IContent['rich']

The RichText field has a few attributes related to the MIME type of what
it stores. These are the default values:

    >>> field.default_mime_type # the default raw/input type
    'text/html'

    >>> field.output_mime_type # the default output type
    'text/x-html-safe'

    >>> field.allowed_mime_types is None # an optional list of allowable types
    True

    >>> field.max_length  # A maximum number of characters (default = None)

These can be set when the field is constructed:

    >>> class IContent(Interface):
    ...     rich = RichText(title=u"Rich text",
    ...                     default_mime_type='text/plain',
    ...                     output_mime_type='text/x-uppercase',
    ...                     allowed_mime_types=('text/plain', 'text/html',),
    ...                     max_length=500)
    >>> field = IContent['rich']

    >>> from persistent import Persistent
    >>> class Content(Persistent):
    ...     implements(IContent)
    ...     def __init__(self, rich=None):
    ...         self.rich = rich

Using the value object
----------------------

The value that is stored on a rich text field is a RichTextValue object.
This object is immutable.

    >>> from plone.app.textfield.value import RichTextValue

The value object stores the 'raw' text value as well as an 'output' value that
is transformed to a target MIME type. It is possible to access the raw value
directly to transform to a different output type if needed, of course.

If no transformation is available, the output will be None.

    >>> value = RichTextValue(raw=u"Some plain text",
    ...                       mimeType='text/plain',
    ...                       outputMimeType=field.output_mime_type,
    ...                       encoding='utf-8')
    >>> value.output is None
    True

To test transformations, we need to provide a transformation engine, via an
ITransformer adapter. For these tests, we will make a rather simple one.

This package comes with a default transformer that uses
Products.PortalTransforms, which in turn comes with Plone.

    >>> from plone.app.textfield.interfaces import ITransformer, TransformError
    >>> from zope.component import adapts, provideAdapter
    >>> class TestTransformer(object):
    ...     implements(ITransformer)
    ...     adapts(Interface)
    ...
    ...     def __init__(self, context):
    ...         self.context = context
    ...
    ...     def __call__(self, value, mimeType):
    ...         if not value.mimeType.startswith('text/'):
    ...             raise TransformError("Can only work with text")
    ...         if mimeType == 'text/x-uppercase':
    ...             return value.raw.upper()
    ...         if mimeType == 'text/x-lowercase':
    ...             return value.raw.lower()
    ...         raise TransformError("Don't know how to create a %s'")
    ...
    >>> provideAdapter(TestTransformer)

Let's now access the output of our previously constructed value object again:

    >>> value.output
    u'SOME PLAIN TEXT'

It is of course possible to get the raw value:

    >>> value.raw
    u'Some plain text'

Or to get the value encoded:

    >>> value.encoding
    'utf-8'
    >>> value.raw_encoded
    'Some plain text'

Converting a value from unicode
-------------------------------

The RichText field provides IFromUnicode:

    >>> from zope.schema.interfaces import IFromUnicode
    >>> IFromUnicode.providedBy(field)
    True

This can be used to create a new RichTextValue from a string, using the
default MIME types set on the field.

    >>> value = field.fromUnicode(u"A plain text string")
    >>> value.mimeType
    'text/plain'
    >>> value.outputMimeType
    'text/x-uppercase'
    >>> value.raw
    u'A plain text string'
    >>> value.raw_encoded
    'A plain text string'
    >>> value.output
    u'A PLAIN TEXT STRING'

Validation
----------

The field will validate the MIME type of the value against the allowed
MIME types if the allowed_mime_types property is set.

    >>> field.allowed_mime_types = None
    >>> field.validate(value)

    >>> field.allowed_mime_types = ('text/html',)
    >>> field.validate(value)
    Traceback (most recent call last):
    ...
    WrongType: (RichTextValue object. (Did you mean <attribute>.raw or <attribute>.output?), ('text/html',))

    >>> field.allowed_mime_types = ('text/plain', 'text/html',)
    >>> field.validate(value)

It will also make sure the raw value is not longer than the max_length,
if a max_length is set.

    >>> long_value = field.fromUnicode(u'x' * (field.max_length + 1))
    >>> field.validate(long_value)
    Traceback (most recent call last):
    ...
    Invalid: msg_text_too_long

Field validation will also check field constraints.

    >>> field.constraint = lambda value: False
    >>> field.validate(value)
    Traceback (most recent call last):
    ...
    ConstraintNotSatisfied: ...


Default value
-------------

The 'default' parameter can be passed to the field upon construction as a
unicode string. It will then be converted to a RichTextValue with default
MIME types.

    >>> default_field = RichText(__name__='default_field',
    ...                          title=u"Rich text",
    ...                          default_mime_type='text/plain',
    ...                          output_mime_type='text/x-uppercase',
    ...                          allowed_mime_types=('text/plain', 'text/html',),
    ...                          default=u"Default value")

    >>> default_field.default
    RichTextValue object. (Did you mean <attribute>.raw or <attribute>.output?)

    >>> default_field.default.raw
    u'Default value'
    >>> default_field.default.outputMimeType
    'text/x-uppercase'
    >>> default_field.default.mimeType
    'text/plain'

Persistence
-----------

The RichTextValue object is not a persistent object.

    >>> from persistent.interfaces import IPersistent
    >>> IPersistent.providedBy(value)
    False

This is on purpose. If it were persistent, it would have its own _p_jar
and so loading an object with a RichTextValue would mean loading two objects
from the ZODB. For the common use case of storing the body text of a content
object (or indeed, any situation where the RichTextValue is usually loaded
when the object is accessed), this is unnecessary overhead.

However, the raw value is stored in a separated persistent object. This means
that unless the 'raw' or 'raw_encoded' attributes are accessed, the raw value
is not loaded from the ZODB.

    >>> value._raw_holder
    <RawValueHolder: A plain text string>

    >>> IPersistent.providedBy(value._raw_holder)
    True

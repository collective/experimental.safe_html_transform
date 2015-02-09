from zope.interface import Attribute
from zope.interface import Interface
from zope import schema

class IPrimaryField(Interface):
    """Marker interface for the primary field in a schema
    """

class IPrimaryFieldInfo(Interface):
    """Information about the primary field of a content item
    
    Content type frameworks should register an adapter to this interface.
    """
    fieldname = Attribute("Field name")
    field = Attribute("Field")
    value = Attribute("Field value")

class IMessageAPI(Interface):
    """Functions provided by this module
    
    These can all be imported as::
    
        >>> from plone.rfc822 import constructMessage
    """
    
    def constructMessageFromSchema(context, schema, charset='utf-8'):
        """Convenience method which calls ``constructMessage()`` with all the
        fields, in order, of the given schema interface
        """
    
    def constructMessageFromSchemata(context, schemata, charset='utf-8'):
        """Convenience method which calls ``constructMessage()`` with all the
        fields, in order, of all the given schemata (a sequence of schema
        interfaces).
        """
    
    def constructMessage(context, fields, charset='utf-8'):
        """Helper method to construct a message.
    
        ``context`` is a content object.
    
        ``fields`` is a sequence of (name, field) pairs for the fields which make
        up the message. This can be obtained from zope.schema.getFieldsInOrder,
        for example.
    
        ``charset`` is the message charset.
    
        The message body will be constructed from the primary field, i.e. the
        field which is marked with ``IPrimaryField``. If no such field exists,
        the message will have no body. If multiple fields exist, the message will
        be a multipart message. Otherwise, it will contain a scalar string
        payload.
    
        A field will be ignored if ``(context, field)`` cannot be multi-adapted
        to ``IFieldMarshaler``, or if the ``marshal()`` method returns None.
        """
    
    def renderMessage(message, mangleFromHeader=False):
        """Render a message to a string
        """
        
    def initializeObjectFromSchema(context, schema, message, defaultCharset='utf-8'):
        """Convenience method which calls ``initializeObject()`` with all the
        fields, in order, of the given schema interface
        """
    
    def initializeObjectFromSchemata(context, schemata, message, defaultCharset='utf-8'):
        """Convenience method which calls ``initializeObject()`` with all the
        fields in order, of all the given schemata (a sequence of schema
        interfaces).
        """

    def initializeObject(context, fields, message, defaultCharset='utf-8'):
        """Initialise an object from a message.
    
        ``context`` is the content object to initialise.
    
        ``fields`` is a sequence of (name, field) pairs for the fields which make
        up the message. This can be obtained from zope.schema.getFieldsInOrder,
        for example.
    
        ``message`` is a ``Message`` object.
    
        ``defaultCharset`` is the default character set to use.
    
        If the message is a multipart message, the primary fields will be read
        in order.
        """

class IFieldMarshaler(Interface):
    """Multi-adapter on (context, field), used for marshalling to and
    demarshalling from RFC2822 message headers.
    
    This interface deals in unicode strings, which will be encoded/decoded
    elsewhere. 
    """
    
    ascii = schema.Bool(
            title=u"ASCII only",
            description=u"Set this to true if this marshaler is guaranteed "
                         "to return ASCII characters only. This will allow "
                         "a header to be rendered without an encoding wrapper",
            default=False,
            required=True,
        )
    
    def marshal(charset='utf-8', primary=False):
        """Return the value of the adapted field on the adapted context.
        
        Note: It may be necessary to adapt the context to the field's
              interface (``field.interface``) before getting the value.
        
        ``charset`` is the default message charset. For string values, you
        should use this charset to encode the string. For binary values,
        it may be appropriate to use a different encoding method.
        
        ``primary`` is set to True if the field being marshalled is a primary
        field, i.e. it will be used in the message body.
        
        The returned value must be a string, or None if there is no value
        in the field.
        
        Raise ``ValueError`` if marshaling is impossible. The field will be
        skipped.
        """
    
    def demarshal(value, message=None, charset='utf-8', contentType=None, primary=False):
        """Update the value of the adapted field on the adapted context.
        
        Note: It may be necessary to adapt the context to the field's
              interface (``field.interface``) before getting the value.
        
        ``value`` is the string value from the message.
        
        ``message`` is the message object itself. This may be None if the
        marshaler is being used in isolation.
        
        ``charset`` is the default charset for the message. For string
        values, this is most likely the encoding of the string. For binary
        values, it may not be.
        
        ``primary`` is set to True if the field being demarshalled is a primary
        field, i.e. it came from the message body.
        
        ``contentType`` is the ``Content-Type`` header from the message, or
        None if this is not available. This is mainly used for primary fields.
        
        Raise ``ValueError`` if the demarshalling cannot be completed.
        """
    
    def encode(value, charset='utf-8', primary=False):
        """Like marshal(), but acts on the passed-in ``value`` instead of
        reading it from the field.
        
        This is only used for collection fields and other situations where
        the value is not read from an instance.
        
        Return None if the value cannot be encoded.
        """
    
    def decode(value, message=None, charset='utf-8', contentType=None, primary=False):
        """Like demarshal, but return the value instead of updating the field.
        
        This is only used for collection fields and other situations where
        the instance should not be updated directly.
        
        Raise ValueError if the value cannot be extracted.
        """
    
    def getContentType():
        """Return the MIME type of the field. The value should be appropriate
        for the Content-Type HTTP header. This is mainly used for marshalling
        the primary field to the message body.
        
        May return None if a content type does not make sense.
        """
    
    def getCharset(defualt='utf-8'):
        """Return the charset of the field. The value should be appropriate
        for the 'charset' parameter to the Content-Type HTTP header. This is
        mainly used for marshalling 
        
        The ``default`` parameter contains the message's default charset.
        
        Must return None if the message should not have a charset, i.e. it
        is not text data.
        """
    
    def postProcessMessage(message):
        """This is a chance to perform any post-processing of the message.
        
        It is only called for primary fields.
        """

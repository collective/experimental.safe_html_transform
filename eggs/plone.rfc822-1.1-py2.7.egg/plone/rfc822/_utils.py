"""Implementation of IMessageAPI methods.

import these from plone.rfc822 directly, not from this module.

See interfaces.py for details.
"""

import logging
from cStringIO import StringIO

# Note: We use capitalised module names to be compatible with Python 2.4
from email.Message import Message 
from email.Header import Header, decode_header
from email.Generator import Generator

from zope.component import queryMultiAdapter
from zope.schema import getFieldsInOrder

from plone.rfc822.interfaces import IFieldMarshaler
from plone.rfc822.interfaces import IPrimaryField

LOG = logging.getLogger('plone.rfc822')

def constructMessageFromSchema(context, schema, charset='utf-8'):
    return constructMessage(context, getFieldsInOrder(schema), charset)

def constructMessageFromSchemata(context, schemata, charset='utf-8'):
    fields = []
    for schema in schemata:
        fields.extend(getFieldsInOrder(schema))
    return constructMessage(context, fields, charset)

def constructMessage(context, fields, charset='utf-8'):
    msg = Message()
    
    primary = []
    
    # First get all headers, storing primary fields for later
    for name, field in fields:
        
        if IPrimaryField.providedBy(field):
            primary.append((name, field,))
            continue
        
        marshaler = queryMultiAdapter((context, field,), IFieldMarshaler)
        if marshaler is None:
            LOG.debug("No marshaler found for field %s of %s" % (name, repr(context)))
            continue
        
        try:
            value = marshaler.marshal(charset, primary=False)
        except ValueError, e:
            LOG.debug("Marshaling of %s for %s failed: %s" % (name, repr(context), str(e)))
            continue
        
        if value is None:
            value = ''
        elif not isinstance(value, str):
            raise ValueError("Marshaler for field %s did not return a string" % name)
        
        if marshaler.ascii and '\n' not in value:
            msg[name] = value
        else:
            msg[name] = Header(value, charset)
    
    # Then deal with the primary field
    
    # If there's a single primary field, we have a non-multipart message with
    # a string payload

    if len(primary) == 1:
        name, field = primary[0]
        
        marshaler = queryMultiAdapter((context, field,), IFieldMarshaler)
        if marshaler is not None:
            contentType = marshaler.getContentType()
            payloadCharset = marshaler.getCharset(charset)
            
            if contentType is not None:
                msg.set_type(contentType)
            
            if payloadCharset is not None:
                # using set_charset() would also add transfer encoding,
                # which we don't want to do always
                msg.set_param('charset', payloadCharset)
                
            value = marshaler.marshal(charset, primary=True)
            if value is not None:
                msg.set_payload(value)
            
            marshaler.postProcessMessage(msg)
    
    # Otherwise, we return a multipart message
    
    elif len(primary) > 1:
        msg.set_type('multipart/mixed')
        
        for name, field in primary:
            
            marshaler = queryMultiAdapter((context, field,), IFieldMarshaler)
            if marshaler is None:
                continue
            
            payload = Message()
            attach = False
            
            contentType = marshaler.getContentType()
            payloadCharset = marshaler.getCharset(charset)
            
            if contentType is not None:
                payload.set_type(contentType)
                attach = True
            if payloadCharset is not None:
                # using set_charset() would also add transfer encoding,
                # which we don't want to do always
                payload.set_param('charset', payloadCharset)
                attach = True
            
            value = marshaler.marshal(charset, primary=True)
            
            if value is not None:
                payload.set_payload(value)
                attach = True
            
            if attach:
                marshaler.postProcessMessage(payload)
                msg.attach(payload)

    return msg

def renderMessage(message, mangleFromHeader=False):
    out = StringIO()
    generator = Generator(out, mangle_from_=mangleFromHeader)
    generator.flatten(message)
    return out.getvalue()

def initializeObjectFromSchema(context, schema, message, defaultCharset='utf-8'):
    initializeObject(context, getFieldsInOrder(schema), message, defaultCharset)

def initializeObjectFromSchemata(context, schemata, message, defaultCharset='utf-8'):
    """Convenience method which calls ``initializeObject()`` with all the
    fields in order, of all the given schemata (a sequence of schema
    interfaces).
    """
    
    fields = []
    for schema in schemata:
        fields.extend(getFieldsInOrder(schema))
    return initializeObject(context, fields, message, defaultCharset)

def initializeObject(context, fields, message, defaultCharset='utf-8'):
    contentType = message.get_content_type()
    
    charset = message.get_charset()
    if charset is None:
        charset = message.get_param('charset')
    if charset is not None:
        charset = str(charset)
    else:
        charset = defaultCharset
    
    headerFields = {}
    primary = []
    
    for name, field in fields:
        if IPrimaryField.providedBy(field):
            primary.append((name, field))
        else:
            headerFields.setdefault(name.lower(), []).append(field)
    
    # Demarshal each header
    
    for name, value in message.items():
        
        name = name.lower()
        fieldset = headerFields.get(name, None)
        if fieldset is None or len(fieldset) == 0:
            LOG.debug("No matching field found for header %s" % name)
            continue
        
        field = fieldset.pop(0)
        
        marshaler = queryMultiAdapter((context, field,), IFieldMarshaler)
        if marshaler is None:
            LOG.debug("No marshaler found for field %s of %s" % (name, repr(context)))
            continue
        
        headerValue, headerCharset = decode_header(value)[0]
        if headerCharset is None:
            headerCharset = charset
        
        # MIME messages always use CRLF. For headers, we're probably safer with \n
        headerValue = headerValue.replace('\r\n', '\n')
        
        try:
            marshaler.demarshal(headerValue, message=message, charset=headerCharset, contentType=contentType, primary=False)
        except ValueError, e:
            # interface allows demarshal() to raise ValueError to indicate marshalling failed
            LOG.debug("Demarshalling of %s for %s failed: %s" % (name, repr(context), str(e)))
            continue
        
    # Then demarshal the primary field
    
    payload = message.get_payload()
    
    # do nothing if we don't have a payload
    if not payload:
        return
    
    # A single string payload
    if isinstance(payload, str):
        if len(primary) != 1:
            raise ValueError("Got a single string payload for message, but no primary fields found for %s" % repr(context))
        else:
            name, field = primary[0]
        
            marshaler = queryMultiAdapter((context, field,), IFieldMarshaler)
            if marshaler is None:
                LOG.debug("No marshaler found for primary field %s of %s" % (name, repr(context),))
            else:
                payloadValue = message.get_payload(decode=True)
                payloadCharset = message.get_content_charset(charset)
                try:
                    marshaler.demarshal(payloadValue, message=message, charset=payloadCharset, contentType=contentType, primary=True)
                except ValueError, e:
                    # interface allows demarshal() to raise ValueError to indicate marshalling failed
                    LOG.debug("Demarshalling of %s for %s failed: %s" % (name, repr(context), str(e)))
        
    # Multiple payloads
    elif isinstance(payload, (list, tuple,)):
        if len(payload) != len(primary):
            raise ValueError("Got %d payloads for message, but %s primary fields found for %s" %  (len(payload), len(primary), repr(context),))
        else:
            for idx, msg in enumerate(payload):
                name, field = primary[idx]
                
                contentType = msg.get_content_type()
    
                charset = message.get_charset()
                if charset is not None:
                    charset = str(charset)
                else:
                    charset = 'utf-8'
                
                marshaler = queryMultiAdapter((context, field,), IFieldMarshaler)
                if marshaler is None:
                    LOG.debug("No marshaler found for primary field %s of %s" % (name, repr(context),))
                    continue
                
                payloadValue = msg.get_payload(decode=True)
                payloadCharset = msg.get_content_charset(charset)
                try:
                    marshaler.demarshal(payloadValue, message=msg, charset=payloadCharset, contentType=contentType, primary=True)
                except ValueError, e:
                    # interface allows demarshal() to raise ValueError to indicate marshalling failed
                    LOG.debug("Demarshalling of %s for %s failed: %s" % (name, repr(context), str(e)))
                    continue

import struct

from zope.interface import implements

from Products.statusmessages.interfaces import IMessage


def _utf8(value):
    if isinstance(value, unicode):
        return value.encode('utf-8')
    elif isinstance(value, str):
        return value
    return ''

def _unicode(value):
    return unicode(value, 'utf-8', 'ignore')


class Message:
    """A single status message.

    Let's make sure that this implementation actually fulfills the
    'IMessage' API.

      >>> from zope.interface.verify import verifyClass
      >>> verifyClass(IMessage, Message)
      True
    
      >>> status = Message(u'this is a test', type=u'info')
      >>> status.message
      u'this is a test'

      >>> status.type
      u'info'

    It is quite common to use MessageID's as status messages:

      >>> from zope.i18nmessageid import MessageFactory
      >>> from zope.i18nmessageid import Message as I18NMessage
      >>> msg_factory = MessageFactory('test')

      >>> msg = msg_factory(u'test_message', default=u'Default text')

      >>> status = Message(msg, type=u'warn')
      >>> status.type
      u'warn'

      >>> type(status.message) is I18NMessage
      True

      >>> status.message.default
      u'Default text'

      >>> status.message.domain
      'test'

    """
    implements(IMessage)

    def __init__(self, message, type=''):
        self.message = message
        self.type = type

    def __eq__(self, other):
        if not isinstance(other, Message):
            return False
        if self.message == other.message and self.type == other.type:
            return True
        return False

    def encode(self):
        """
        Encode to a cookie friendly format.
        
        The format consists of a two bytes length header of 11 bits for the
        message length and 5 bits for the type length followed by two values.
        """
        message = _utf8(self.message)[:0x3FF] # we can store 2^11 bytes
        type = _utf8(self.type)[:0x1F]        # we can store 2^5 bytes
        size = (len(message) << 5) + (len(type) & 31) # pack into 16 bits
        
        return struct.pack('!H%ds%ds' % (len(message), len(type)), 
                           size, message, type)

def decode(value):
    """
    Decode messages from a cookie

    We return the decoded message object, and the remainder of the cookie
    value (it can contain further messages).

    We expect at least 2 bytes (size information).
    """
    if len(value) >= 2:
        size = struct.unpack('!H', value[:2])[0]
        msize, tsize = (size >> 5, size & 31)
        message = Message(_unicode(value[2:msize+2]),
                          _unicode(value[msize+2:msize+tsize+2]))
        return message, value[msize+tsize+2:]
    return None, ''

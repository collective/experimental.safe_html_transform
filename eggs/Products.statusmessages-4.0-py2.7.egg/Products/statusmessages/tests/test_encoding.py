"""
    Encoding tests.
"""

import unittest

def test_encoding():
    r"""
    Test message encoding:

      >>> from Products.statusmessages.message import Message
      >>> from Products.statusmessages.message import decode

      >>> m = Message(u'spam', u'eggs')
      >>> m.encode()
      '\x00\x84spameggs'

      >>> decode(m.encode())[0] == m
      True

      >>> m = Message(u'spam')
      >>> m.encode()
      '\x00\x80spam'

      >>> decode(m.encode())[0] == m
      True
    """

def test_decoding():
    r"""
    Test message decoding:

      >>> from Products.statusmessages.message import Message
      >>> from Products.statusmessages.message import decode

    Craft a wrong value:

      >>> m, rem = decode('\x01\x84spameggs')
      >>> m.message, m.type
      (u'spameggs', u'')

      >>> rem
      ''

    Craft another wrong value:

      >>> m, rem = decode('\x00\x24spameggs')
      >>> m.message, m.type
      (u's', u'pame')

      >>> rem
      'ggs'

    And another wrong value:

      >>> m, rem = decode('\x00spameggs')
      >>> m.message, m.type
      (u'pam', u'eggs')

      >>> rem
      ''

    And yet another wrong value:

      >>> m, rem = decode('')
      >>> m is None, rem is ''
      (True, True)
    """


def test_suite():
    from Testing.ZopeTestCase import ZopeDocTestSuite
    return ZopeDocTestSuite()

if __name__ == '__main__':
    unittest.main(defaultTest="test_suite")

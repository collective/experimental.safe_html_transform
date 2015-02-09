# -*- coding: UTF-8 -*-
"""
    StatusMessage adapter tests.
"""

import unittest

def test_directives():
    """
    Test status messages

    First some boilerplate.

      >>> from zope.component.testing import setUp
      >>> setUp()

      >>> import Products.Five
      >>> import Products.statusmessages

      >>> from Products.Five import zcml
      >>> zcml.load_config('meta.zcml', Products.Five)
      >>> zcml.load_config('configure.zcml', Products.statusmessages)

    Now lets make sure we can actually adapt the request.

      >>> from Products.statusmessages.interfaces import IStatusMessage
      >>> status = IStatusMessage(self.app.REQUEST)
      >>> IStatusMessage.providedBy(status)
      True

    We also need the request to be annotatable:

      >>> from zope.interface import directlyProvides
      >>> from zope.annotation.interfaces import IAttributeAnnotatable
      >>> directlyProvides(self.app.REQUEST, IAttributeAnnotatable)

    The dummy request we have is a bit limited, so we need a simple method
    to fake a real request/response for the cookie handling. Basically it
    puts all entries from response.cookies into REQUEST.cookies but shifts
    the real values into the right place as browsers would do it.
      
      >>> def fakePublish(request):
      ...     cookies = request.response.cookies.copy()
      ...     new_cookies = {}
      ...     for key in cookies.keys():
      ...         new_cookies[key] = cookies[key]['value']
      ...     request.cookies = new_cookies
      ...     request.response.cookies = {}

      >>> request = self.app.REQUEST
      >>> status = IStatusMessage(request)

    Make sure there's no stored message.

      >>> len(status.show())
      0

    Add one message
      
      >>> status.add(u'test', type=u'info')

    Now check the results

      >>> messages = status.show()
      >>> len(messages)
      1

      >>> messages[0].message
      u'test'

      >>> messages[0].type
      u'info'

    Make sure messages are removed

      >>> len(status.show())
      0

    Since we accessed the message prior to publishing the page, we must 
    ensure that the messages have been removed from the cookies

      >>> fakePublish(request)
      >>> len(status.show())
      0

    Now we repeat the test, only this time we publish the page prior to
    retrieving the messages

    Add one message
      
      >>> status.add(u'test', type=u'info')

    Publish the request

      >>> fakePublish(request)

    Now check the results

      >>> messages = status.show()
      >>> len(messages)
      1

      >>> messages[0].message
      u'test'

      >>> messages[0].type
      u'info'

    Make sure messages are removed

      >>> len(status.show())
      0

    Add two messages (without publishing)

      >>> status.add(u'test', type=u'info')
      >>> status.add(u'test1', u'warn')
      
    And check the results again

      >>> messages = status.show()
      >>> len(messages)
      2

      >>> test = messages[1]

      >>> test.message
      u'test1'

      >>> test.type
      u'warn'

    Make sure messages are removed again

      >>> len(status.show())
      0

    Add two messages (with publishing)

      >>> status.add(u'test', type=u'info')
      >>> fakePublish(request)
      >>> status.add(u'test1', u'warn')
      
    And check the results again

      >>> fakePublish(request)
      >>> messages = status.show()
      >>> len(messages)
      2

      >>> test = messages[1]

      >>> test.message
      u'test1'

      >>> test.type
      u'warn'

    Make sure messages are removed again

      >>> len(status.show())
      0

    Add two identical messages

      >>> status.add(u'test', type=u'info')
      >>> status.add(u'test', type=u'info')

    And check the results again

      >>> fakePublish(request)
      >>> messages = status.show()
      >>> len(messages)
      1

      >>> test = messages[0]

      >>> test.message
      u'test'

      >>> test.type
      u'info'

    Make sure messages are removed again

      >>> len(status.show())
      0

    Test incredibly long messages:

      >>> status.add(u'm' * 0x400, type=u't' * 0x20)

      And check the results again

      >>> fakePublish(request)
      >>> messages = status.show()
      >>> len(messages)
      1

      >>> test = messages[0]

      >>> test.message == u'm' * 0x3FF
      True

      >>> test.type == u't' * 0x1F
      True
      
    Messages are stored as base64-ed cookie values, so we must make sure we
    create proper header values; all ascii characters, and no newlines:
    
      >>> status.add(u'test' * 40, type=u'info')
      >>> cookies = [c['value'] for c in request.response.cookies.values()]
      >>> cookies = ''.join(cookies)
      >>> cookies == unicode(cookies).encode('ASCII')
      True
      >>> '\\n' in cookies
      False

      >>> from zope.component.testing import tearDown
      >>> tearDown()
    """

def test_301():
    """
    Test status messages for 301/302/304 request

    First some boilerplate.

      >>> from zope.component.testing import setUp
      >>> setUp()

      >>> import Products.Five
      >>> import Products.statusmessages

      >>> from Products.Five import zcml
      >>> zcml.load_config('meta.zcml', Products.Five)
      >>> zcml.load_config('configure.zcml', Products.statusmessages)

      >>> from zope.interface import directlyProvides
      >>> from zope.annotation.interfaces import IAttributeAnnotatable
      >>> directlyProvides(self.app.REQUEST, IAttributeAnnotatable)
      
      >>> from Products.statusmessages.interfaces import IStatusMessage

      >>> def fakePublish(request, status=200):
      ...     cookies = request.response.cookies.copy()
      ...     new_cookies = {}
      ...     for key in cookies.keys():
      ...         new_cookies[key] = cookies[key]['value']
      ...     request.cookies = new_cookies
      ...     request.response.cookies = {}
      ...     request.response.setStatus(status)

      >>> request = self.app.REQUEST
      >>> status = IStatusMessage(request)

    Make sure there's no stored message.

      >>> len(status.show())
      0

    Add one message
      
      >>> status.add(u'test', type=u'info')

    Publish a redirect response that also happened to call show(). This could
    happen if the redirect (unnecessarily) rendered a template showing the
    status message, for example.
    
      >>> fakePublish(request, 302)
      >>> messages = status.show()
      >>> len(messages)
      1

      >>> messages[0].message
      u'test'

      >>> messages[0].type
      u'info'

    Make sure messages are not removed - we really want them to show the
    next time around, when the redirect has completed.

      >>> len(status.show())
      1

    Let's now fake redirection. The message should still be there, but will
    then be expired.
    
      >>> fakePublish(request, 200)
      >>> messages = status.show()
      >>> len(messages)
      1

      >>> messages[0].message
      u'test'

      >>> messages[0].type
      u'info'
    
    The message should now be gone.
      
      >>> len(status.show())
      0

      >>> from zope.component.testing import tearDown
      >>> tearDown()
    """

def test_suite():
    from Testing.ZopeTestCase import ZopeDocTestSuite
    return ZopeDocTestSuite()

if __name__ == '__main__':
    unittest.main(defaultTest="test_suite")

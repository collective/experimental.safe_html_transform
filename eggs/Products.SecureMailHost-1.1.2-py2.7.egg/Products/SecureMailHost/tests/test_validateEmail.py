#
# Tests the email validation
#

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *

class TestValidateEmail(ZopeTestCase.ZopeTestCase):

    def afterSetUp(self):
        self.mailhost = SecureMailBase('securemailhost', '')

    def testvalidateSingleEmailAddress(self):
        # Any RFC 822 email address allowed, but address list must fail
        val = self.mailhost.validateSingleEmailAddress
        validInputs = (
            'user@example.org',
            'user@host.example.org',
            'm@t.nu',
            'm+m@example.biz',
            'm.+m@example.info',
            'foo&.%#$&\'*+-/=?^_`{}|~bar@baz.org'

            ## Some trickier ones, from RFC 822
            #'"A Name" user @ example',
            #'"A Name" user\n @ example',
            #'nn@[1.2.3.4]'
        )
        invalidInputs = (
            'user@foo', # rfc 822 requires the domain part
            'user@example.org, user2@example.org',   # only single address allowed
            'user@example.org,user2@example.org',
            #'user@example.org;user2@example.org',
            'user@example.org\n\nfoo', # double new lines
            'user@example.org\n\rfoo',
            'user@example.org\r\nfoo',
            'user@example.org\r\rfoo',
            'user@example.org\nfoo@example.org', # only single address allowed, even if given one per line
            'user@example.org\nBcc: user@example.org',
            'user@example.org\nCc: user@example.org',
            'user@example.org\nSubject: Spam',
            # and a full email (note the missing ,!)
            'From: foo@example.org\n'
            'To: bar@example.org, spam@example.org\n'
            'Cc: egg@example.org\n'
            'Subject: Spam me plenty\n'
            'Spam Spam Spam\n'
            'I hate spam',
            
        )
        for address in validInputs:
            self.failUnless(val(address), '%s should validate' % address)
        for address in invalidInputs:
            self.failIf(val(address), '%s should fail' % address)
    
    def testvalidateEmailAddresses(self):
        # Any RFC 822 email address allowed and address list allowed
        val = self.mailhost.validateEmailAddresses

        validInputs = (
            'user@example.org',
            'foo&.%#$&\'*+-/=?^_`{}|~bar@baz.org,\n foo&.%#$&\'*+-/=?^_`{}|~bar@baz.org',
            'user@example.org,\n user2@example.org',
            'user@example.org\n user2@example.org' # omitting comma is ok
        )
        invalidInputs = (
            'user@example.org\n\nfoo', # double new lines
            'user@example.org\n\rfoo',
            'user@example.org\r\nfoo',
            'user@example.org\r\rfoo',
            #py stdlib bug? 'user@example.org\nuser2@example.org', # continuation line doesn't begin with white space
        )
        for address in validInputs:
            self.failUnless(val(address), '%s should validate' % address)
        for address in invalidInputs:
            self.failIf(val(address), '%s should fail' % address)

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestValidateEmail))
    return suite

if __name__ == '__main__':
    framework()

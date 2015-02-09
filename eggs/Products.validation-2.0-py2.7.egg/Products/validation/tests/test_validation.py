
from Testing import ZopeTestCase
from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Testing.ZopeTestCase import doctest

from Products.validation import validation

class TestValidation(ATSiteTestCase):

    def test_inNumericRange(self):
        v = validation.validatorFor('inNumericRange')
        self.failUnlessEqual(v(10, 1, 20), 1)
        self.failUnlessEqual(v('10', 1, 20), 1)
        self.failUnlessEqual(v(0, 4, 5), u"Validation failed(inNumericRange): '0' out of range(4, 5)")

    def test_isDecimal(self):
        v = validation.validatorFor('isDecimal')
        self.failUnlessEqual(v('1.5'), 1)
        self.failUnlessEqual(v('1,5'), 1)
        self.failUnlessEqual(v('NaN'), u"Validation failed(isDecimal): 'NaN' is not a decimal number.")

    def test_isPrintable(self):
        v = validation.validatorFor('isPrintable')
        self.failUnlessEqual(v('text'), 1)
        self.failUnlessEqual(v('\u203'), u"Validation failed(isPrintable): '\\u203' contains unprintable characters")
        self.failUnlessEqual(v(10), u"Validation failed(isPrintable): 10 of type <type 'int'>, expected 'string'")

    def test_isSSN(self):
        v = validation.validatorFor('isSSN')
        self.failUnlessEqual(v('111223333'), 1)
        self.failUnlessEqual(v('111-22-3333', ignore=r'-'), 1)

    def test_isUSPhoneNumber(self):
        v = validation.validatorFor('isUSPhoneNumber')
        self.failUnlessEqual(v('(212) 555-1212',
                               ignore=r'[\s\(\)\-]'), 1)
        self.failUnlessEqual(v('2125551212',
                               ignore=r'[\s\(\)\-]'), 1)

        self.failUnlessEqual(v('(212) 555-1212'), 1)

    def test_isURL(self):
        v = validation.validatorFor('isURL')
        self.failUnlessEqual(v('http://foo.bar:8080/manage'), 1)
        self.failUnlessEqual(v('https://foo.bar:8080/manage'), 1)
        self.failUnlessEqual(v('irc://tiran@irc.freenode.net:6667/#plone'), 1)
        self.failUnlessEqual(v('fish://tiran:password@myserver/~/'), 1)
        self.failUnlessEqual(v('http://\n'), u"Validation failed(isURL): 'http://\n' is not a valid url.")
        self.failIfEqual(v('../foo/bar'), 1)

    def test_isEmail(self):
        v = validation.validatorFor('isEmail')
        self.failUnlessEqual(v('test@test.com'), 1)
        self.failIfEqual(v('@foo.bar'), 1)
        self.failUnlessEqual(v('me'), u"Validation failed(isEmail): 'me' is not a valid email address.")

    def test_isMailto(self):
        v = validation.validatorFor('isMailto')
        self.failUnlessEqual(v('mailto:test@test.com'), 1)
        self.failIfEqual(v('test@test.com'), 1)
        self.failIfEqual(v('mailto:@foo.bar'), 1)
        self.failIfEqual(v('@foo.bar'), 1)
        self.failIfEqual(v('mailto:'), 1)
        self.failUnlessEqual(v('me'), u"Validation failed(isMailto): 'me' is not a valid email address.")

    def test_isUnixLikeName(self):
        v = validation.validatorFor('isUnixLikeName')
        self.failUnlessEqual(v('abcd'), 1)
        self.failUnless(v('a_123456'), 1)
        self.failIfEqual(v('123'), 1)
        self.failIfEqual(v('ab.c'), 1)
        self.failUnlessEqual(v('ab,c'), u"Validation failed(isUnixLikeName): 'ab,c' this name is not a valid identifier")
        self.failIfEqual(v('aaaaaaaab'), 1) # too long

    def test_isValidId(self):
        v = validation.validatorFor("isValidId")
        self.failUnlessEqual(v("a b", object()), u"Spaces are not allowed in ids")
        # TODO: more tests require a site


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestValidation))

    doctests = (
        'Products.validation.validators.ExpressionValidator',
        )
    for module in doctests:
        suite.addTest(doctest.DocTestSuite(module))

    return suite

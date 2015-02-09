from Products.Five.testbrowser import Browser
from Products.PloneTestCase import ptc
from plone.app.imaging import testing
from plone.app.imaging.tests.utils import getData
from StringIO import StringIO


ptc.setupPloneSite()


class ImagingTestCaseMixin:
    """ mixin for integration and functional tests """

    def getImage(self, name='image.gif'):
        return getData(name)

    def assertImage(self, data, format, size):
        import PIL.Image
        image = PIL.Image.open(StringIO(data))
        self.assertEqual(image.format, format)
        self.assertEqual(image.size, size)


class ImagingTestCase(ptc.PloneTestCase, ImagingTestCaseMixin):
    """ base class for integration tests """

    layer = testing.imaging


class ImagingFunctionalTestCase(ptc.FunctionalTestCase, ImagingTestCaseMixin):
    """ base class for functional tests """

    layer = testing.imaging

    def getCredentials(self):
        return '%s:%s' % (ptc.default_user, ptc.default_password)

    def getBrowser(self, loggedIn=True):
        """ instantiate and return a testbrowser for convenience """
        browser = Browser()
        if loggedIn:
            auth = 'Basic %s' % self.getCredentials()
            browser.addHeader('Authorization', auth)
        return browser

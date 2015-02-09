from Testing import ZopeTestCase
from Testing.ZopeTestCase import installPackage
from Products.PloneTestCase import ptc
from Products.PloneTestCase.layer import onsetup, PloneSite
from wicked.testing.xml import xstrip as strip
from wicked.normalize import titleToNormalizedId
from wicked.registration import BasePloneWickedRegistration
from Products.Five import zcml

TITLE1 = "Cop Shop"
TITLE2 = 'DMV Computer has died'

import transaction as txn
#from collective.testing.debug import autopsy

@onsetup
def register_package():
    import wicked.atcontent
    zcml.load_config("configure.zcml", package=wicked.atcontent)
    installPackage('wicked.atcontent')

register_package()
ptc.setupPloneSite(products=['wicked.atcontent'])

class WickedSite(PloneSite):

    @classmethod
    def setUp(cls):
        app = ZopeTestCase.app()
        plone = app.plone
        reg = BasePloneWickedRegistration(plone)
        reg.handle()
        # install the product
        qi = plone.portal_quickinstaller
        qi.installProduct('wicked.atcontent')
        txn.commit()
        ZopeTestCase.close(app)

    @classmethod
    def tearDown(cls):
        app = ZopeTestCase.app()
        plone = app.plone
        reg = BasePloneWickedRegistration(plone)
        reg.handle(unregister=True)
        txn.commit()
        ZopeTestCase.close(app)

# This is the test case. You will have to add test_<methods> to your
# class in order to assert things about your Product.
class WickedTestCase(ptc.PloneTestCase):

    layer = WickedSite
    setter = 'setBody'

    def set_text(self, content, text, **kw):
        setter = getattr(content, self.setter)
        setter(text, **kw)

    def afterSetUp(self):
        #self.loginAsPortalOwner()
        # add some pages
        id1 = titleToNormalizedId(TITLE1)
        id2 = titleToNormalizedId(TITLE2)
        self.page1 = makeContent(self.folder,id1,self.wicked_type,title=TITLE1)
        self.page2 = makeContent(self.folder,id2,self.wicked_type, title=TITLE2)

    strip = staticmethod(strip)

    def getRenderedWickedField(self, doc):
        fieldname = self.wicked_field
        text = doc.getField(fieldname).get(doc)
        return self.strip(text)

    def failIfAddLink(self, doc):
        """ does wicked field text contain a wicked-generated add link? """
        # XXX make test stronger, support looking for specific links
        home_url= doc.absolute_url()
        text = self.getRenderedWickedField(doc)
        if home_url in text:
            self.fail("%s FOUND:\n\n %s" %(home_url, text))

    def failUnlessAddLink(self, doc):
        """ does wicked field text contain a wicked-generated add link? """
        # XXX make test stronger, support looking for specific links
        home_url= doc.absolute_url()
        text = self.getRenderedWickedField(doc)
        if not home_url in text:
            self.fail("%s NOT FOUND:\n\n %s" %(home_url, text))

    def failIfWickedLink(self, doc, dest):
        dest = dest.absolute_url()
        text = self.getRenderedWickedField(doc)
        if dest in text:
            self.fail("%s FOUND:\n\n %s" %(dest, text))

    failIfMatch = failIfWickedLink

    def failUnlessWickedLink(self, doc, dest):
        dest = dest.absolute_url()
        text = self.getRenderedWickedField(doc)
        if not dest in text:
            self.fail("%s NOT FOUND:\n\n %s" %(dest, text))

    failUnlessMatch = failUnlessWickedLink

    def hasAddLink(self, doc):
        """ does wicked field text contain a wicked-generated add link? """
        # XXX make test stronger, support looking for specific links
        return doc.absolute_url() in self.getRenderedWickedField(doc)

    def hasWickedLink(self, doc, dest):
        """ does wicked field text contain a resolved wicked link to
        the specified dest object?  """
        # XXX make test stronger
        return dest.absolute_url() in self.getRenderedWickedField(doc)



def makeContent(container, id, portal_type, **kw):
    container.invokeFactory(id=id, type_name=portal_type, **kw)
    o = getattr(container, id)
    return o

import os, sys, time
import unittest
from sets import Set
import traceback
from Testing import ZopeTestCase
from wickedtestcase import WickedTestCase, makeContent, TITLE2
from wicked.normalize import titleToNormalizedId
from wicked.at.config import BACKLINK_RELATIONSHIP
from Products.CMFCore.utils import getToolByName

class Base(WickedTestCase):
    wicked_type = 'IronicWiki'
    wicked_field = 'body'

    def replaceCreatedIndex(self):
        """ replace the 'created' index w/ a field index b/c we need
        better than 1 minute resolution for our testing """
        cat = getToolByName(self.portal, 'portal_catalog')
        cat.delIndex('created')
        cat.manage_addIndex('created', 'FieldIndex',
                            extra={'indexed_attrs':'created'})
        cat.manage_reindexIndex(ids=['created'])

    def demoCreate(self, **kw):
        self.login('test_user_1_')
        addview = self.page1.restrictedTraverse('@@wickedadd')
        addview.add_content(title=self.title, section=self.wicked_field, type_name=self.wicked_type)

    def moveContent(self, obj, target):
        cps = obj.aq_parent.manage_copyObjects([obj.getId()])
        target.manage_pasteObjects(cps)



class TestWikiLinking(Base):

    def afterSetUp(self):
        super(TestWikiLinking, self).afterSetUp()
        self.set_text(self.page1, '((%s))' % TITLE2)

    def test_backlink(self):
        assert self.page1 in self.page2.getRefs(relationship=BACKLINK_RELATIONSHIP)

    def test_backlink_after_wickedadd(self):
        '''
        Test that the backlink is set if the link is added first
        and the content is created afterwards with the @@wickedadd link
        '''
        TITLE = 'lowertitle'
        self.login('test_user_1_')
        self.set_text(self.page1, '((%s))' % TITLE)
        addview = self.page1.restrictedTraverse('@@wickedadd')
        addview.add_content(title=TITLE,
                            section=self.wicked_field,
                            type_name=self.wicked_type)
        newcontent = self.folder[TITLE]
        assert self.page1 in newcontent.getRefs(relationship=BACKLINK_RELATIONSHIP)

    def testforlink(self):
        self.failUnlessWickedLink(self.page1, self.page2)

    def testformultiplelinks(self):
        self.set_text(self.page1, '((DMV Computer has died))  ((Make another link))')
        self.failUnlessAddLink(self.page1)

        self.failUnlessWickedLink(self.page1, self.page2)

    def testInexactTitleNotMatch(self):
        w1 = makeContent(self.folder, 'w1', self.wicked_type,
                         title='W1 Title With Extra')
        self.set_text(self.page1, "((W1 Title))")
        self.failIfWickedLink(self.page1, w1)
        self.failUnlessAddLink(self.page1)

    def testInexactTitleNotBlockLocalId(self):
        w1 = makeContent(self.folder, 'w1', self.wicked_type,
                         title='W1 Title')
        w2 = makeContent(self.folder, 'w2', self.wicked_type,
                         title='%s With Extra' % w1.id)
        self.set_text(self.page1, "((%s))" % w1.id)
        self.failUnlessWickedLink(self.page1, w1)
        self.failIfWickedLink(self.page1, w2)

    def testInexactLocalTitleNotBlockLocalTitle(self):
        w1 = makeContent(self.folder, 'w1', self.wicked_type,
                         title='W1 Title')
        w2 = makeContent(self.folder, 'w2', self.wicked_type,
                         title='%s With Extra' % w1.Title())
        self.set_text(self.page1, "((%s))" % w1.Title())
        self.failUnlessWickedLink(self.page1, w1)
        self.failIfWickedLink(self.page1, w2)

    def testInexactRemoteTitleNotBlockRemoteId(self):
        f2 = makeContent(self.folder, 'f2', 'Folder')
        w1 = makeContent(self.folder, 'w1', self.wicked_type,
                         title='W1 Title')
        w2 = makeContent(self.folder, 'w2', self.wicked_type,
                         title='%s With Extra' % w1.id)
        w3 = makeContent(f2, 'w3', self.wicked_type,
                         title='W3 Title')
        self.set_text(w3, "((%s))" % w1.id)
        self.failUnlessWickedLink(w3, w1)
        self.failIfWickedLink(w3, w2)

    def testInexactRemoteTitleNotBlockRemoteTitle(self):
        f2 = makeContent(self.folder, 'f2', 'Folder')
        w1 = makeContent(self.folder, 'w1', self.wicked_type,
                         title='W1 Title')
        w2 = makeContent(self.folder, 'w2', self.wicked_type,
                         title='%s With Extra' % w1.Title())
        w3 = makeContent(f2, 'w3', self.wicked_type,
                         title='W3 Title')
        self.set_text(w3, "((%s))" % w1.Title())
        self.failUnlessWickedLink(w3, w1)
        self.failIfWickedLink(w3, w2)

    def testDupLocalTitleMatchesOldest(self):
        self.replaceCreatedIndex()
        title = 'Duplicate Title'
        w1 = makeContent(self.folder, 'w1', self.wicked_type,
                         title=title)
        w2 = makeContent(self.folder, 'w2', self.wicked_type,
                         title=title)
        w3 = makeContent(self.folder, 'w3', self.wicked_type,
                         title=title)
        self.set_text(self.page1, "((%s))" % title)
        self.failUnlessWickedLink(self.page1, w1)

        # this also tests that deleting uncaches
        self.folder.manage_delObjects(ids=[w1.getId()])

        self.failUnlessWickedLink(self.page1, w2)

    def testDupRemoteIdMatchesOldest(self):
        self.replaceCreatedIndex()
        id = 'duplicate_id'
        f2 = makeContent(self.folder, 'f2', 'Folder')
        f3 = makeContent(self.folder, 'f3', 'Folder')
        f4 = makeContent(self.folder, 'f4', 'Folder')
        w1 = makeContent(f2, id, self.wicked_type,
                         title='W1 Title')
        # mix up the order, just to make sure
        w3 = makeContent(f4, id, self.wicked_type,
                         title='W3 Title')
        w2 = makeContent(f3, id, self.wicked_type,
                         title='W2 Title')
        self.set_text(self.page1, "((%s))" % id)
        self.failIfWickedLink(self.page1, w2)
        self.failIfWickedLink(self.page1, w3)
        self.failUnlessWickedLink(self.page1, w1)

        f2.manage_delObjects(ids=[w1.id])
        self.failIfWickedLink(self.page1, w2)

        # fails due to caching
        self.failUnlessWickedLink(self.page1, w3)

    def makeFolders(self, *args):
        folders = list()
        for id in args:
            folders.append(makeContent(self.folder, id, 'Folder'))
        return tuple(folders)

    def testDupRemoteTitleMatchesOldest(self):
        self.replaceCreatedIndex()
        title = 'Duplicate Title'

        f2, f3, f4 = self.makeFolders('f2', 'f3', 'f4')

        w1 = makeContent(f2, 'w1', self.wicked_type,
                         title=title)
        # mix up the order, just to make sure
        w3 = makeContent(f4, 'w3', self.wicked_type,
                         title=title)
        w2 = makeContent(f3, 'w2', self.wicked_type,
                         title=title)
        self.set_text(self.page1, "((%s))" % title)
        self.failUnlessWickedLink(self.page1, w1)
        self.failIfWickedLink(self.page1, w2)
        self.failIfWickedLink(self.page1, w3)

        f2.manage_delObjects(ids=[w1.id])
        self.failUnlessWickedLink(self.page1, w3)
        self.failIfWickedLink(self.page1, w2)

    def testLinkPersistsThroughMove(self):
        title = 'Move Me'
        f2, f3 = self.makeFolders('f2', 'f3')
        w1 = makeContent(f2, 'w1', self.wicked_type,
                         title=title)

        # check implicit resolution
        # this is a pre-test
        # should set cache
        self.set_text(self.page1, "((%s))" % title)
        self.failUnlessWickedLink(self.page1, w1)

        # move w1
        self.moveContent(w1, f3)

        w1.setTitle('new title to make sure we do not accidentally resolve')

        # check link did not change
        self.failUnlessWickedLink(self.page1, w1)

class TestDocCreation(Base):

    def afterSetUp(self):
        WickedTestCase.afterSetUp(self)
        self.title = 'Create a New Document'
        self.demoCreate()
        self.set_text(self.page1, '((%s))' %self.title)

    def testDocAdded(self):
        self.failUnless(getattr(self.folder,
                                titleToNormalizedId(self.title), None))

    def testBacklinks(self):
        newdoc = getattr(self.folder, titleToNormalizedId(self.title))
        backlinks = newdoc.getRefs(relationship=BACKLINK_RELATIONSHIP)
        self.failUnless(self.page1 in backlinks)

class TestLinkNormalization(Base):
    title = 'the monkey flies at dawn'

    def afterSetUp(self):
        super(TestLinkNormalization, self).afterSetUp()
        title1 = self.title
        self.login('test_user_1_')
        self.newpage = self.clickCreate(self.page1, self.title)

    def clickCreate(self, page, title):
        """
        simulates browser interaction
        """
        addview = page.restrictedTraverse('@@wickedadd')
        addview.add_content(title=title, section=self.wicked_field, type_name=self.wicked_type)
        self.set_text(page, "((%s))" %title ) #wha?
        return getattr(self.folder, titleToNormalizedId(title))

# @@ demonstrates issue with ids that are not tightly coupled to Title
# as of 1.0.1 still fails
##     def test_oldTitleWinsNewId(self):
##         # this will should fail
##         # if title changes don't trigger
##         # id changes
##         self.replaceCreatedIndex()
##         newtitle = 'I changed my mind'
##         self.page2.update(**dict(title=self.title))
##         self.newpage.update(**dict(title=newtitle))

##         # page one should still link to new page
##         # even though page2 has same title as link
##         self.failUnlessWickedLink(self.page1, self.newpage)

##         # delete newpage and recreate
##         # older title should beat newer id
##         self.loginAsPortalOwner()
##         self.folder.manage_delObjects([self.newpage.getId()])
##         self.newpage = self.clickCreate(self.page2, self.title)

##         self.failIfWickedLink(self.page1, self.newpage)
##         self.failUnlessWickedLink(self.page1, self.page2)


    def test_create_titlechange(self):
        # add content from link
        # test link
        # change title
        # test link
        title1 = self.title

        # if this fails, wicked is not working period
        self.failUnlessWickedLink(self.page1, self.newpage)

        self.newpage.update(**dict(title='I changed my mind'))
        self.failUnlessWickedLink(self.page1, self.newpage)

class TestRemoteLinking(Base):

    def afterSetUp(self):
        super(TestRemoteLinking, self).afterSetUp()
        self.set_text(self.page1, '((%s))' % TITLE2)

    def testLocalIdBeatsRemoteId(self):
        self.replaceCreatedIndex()
        f2 = makeContent(self.folder, 'f2', 'Folder')
        w1 = makeContent(f2, self.page1.getId(), self.wicked_type,
                         title='W1 Title')
        w2 = makeContent(f2, 'w2_id', self.wicked_type,
                         title='W2 Title')
        self.set_text(w2, "((%s))" % self.page1.getId())
        self.failIfWickedLink(w2, self.page1)
        self.failUnlessWickedLink(w2, w1)

    def testLocalTitleBeatsRemoteId(self):
        self.replaceCreatedIndex()
        f2 = makeContent(self.folder, 'f2', 'Folder')
        w1 = makeContent(f2, 'w1_id', self.wicked_type,
                         title=self.page1.id)
        w2 = makeContent(f2, 'w2_id', self.wicked_type,
                         title='W2 Title')
        self.set_text(w2, "((%s))" % self.page1.id)
        self.failUnlessWickedLink(w2, w1)
        self.failIfWickedLink(w2, self.page1)

    def testInexactLocalTitleNotBlockRemoteTitle(self):
        f2 = makeContent(self.folder, 'f2', 'Folder')
        w1 = makeContent(self.folder, 'w1', self.wicked_type,
                         title='W1 Title')
        w2 = makeContent(f2, 'w2', self.wicked_type,
                         title='%s With Extra' % w1.Title())
        w3 = makeContent(f2, 'w3', self.wicked_type,
                         title='W3 Title')
        self.set_text(w3, "((%s))" % w1.Title())
        self.failUnlessWickedLink(w3, w1)
        self.failIfWickedLink(w3, w2)

    def testInexactLocalTitleNotBlockRemoteId(self):
        f2 = makeContent(self.folder, 'f2', 'Folder')
        w1 = makeContent(self.folder, 'w1', self.wicked_type,
                         title='W1 Title')
        w2 = makeContent(f2, 'w2', self.wicked_type,
                         title='%s With Extra' % w1.id)
        w3 = makeContent(f2, 'w3', self.wicked_type,
                         title='W3 Title')
        self.set_text(w3, "((%s))" % w1.id)
        self.failUnlessWickedLink(w3, w1)
        self.failIfWickedLink(w3, w2)


def test_suite():
    from wicked.at.link import test_suite as btests
    suites = [unittest.makeSuite(tc) for tc in TestDocCreation, TestWikiLinking, TestLinkNormalization, TestRemoteLinking]
    suites.append(btests())
    suite = unittest.TestSuite(suites)
    return suite


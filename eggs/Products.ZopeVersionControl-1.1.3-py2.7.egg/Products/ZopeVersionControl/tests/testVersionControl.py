##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################
""" Test the ZVC machinery

$Id: testVersionControl.py 113728 2010-06-21 15:10:46Z ctheune $
"""
import unittest

from common import get_transaction
from common import common_setUp
from common import common_tearDown
from common import common_commit

class VersionControlTests(unittest.TestCase):
 
    setUp = common_setUp
    tearDown = common_tearDown
    commit = common_commit

    do_commits = 0

    def testIsVersionableResource(self):
        # Test checking whether an object is a versionable resource.
        repository = self.repository
        document = self.document1
        nonversionable = self.document_nonversion
        self.failUnless(repository.isAVersionableResource(document))
        self.failIf(repository.isAVersionableResource(nonversionable))
        self.failIf(repository.isAVersionableResource('foobar'))
        self.failIf(repository.isAVersionableResource(self))


    def testIsUnderVersionControl(self):
        # Test checking whether an object is under version control.
        repository = self.repository
        document = self.document1
        self.failIf(repository.isUnderVersionControl(document))
        repository.applyVersionControl(document)
        self.commit()
        self.failUnless(repository.isUnderVersionControl(document))


    def testIsResourceUpToDate(self):
        # Test checking whether a versioned resource is up to date.
        repository = self.repository
        document = repository.applyVersionControl(self.document1)
        self.commit()
        self.failUnless(repository.isResourceUpToDate(document))

        info = repository.getVersionInfo(document)
        first_version = info.version_id

        document = repository.checkoutResource(document)
        self.commit()
        document = repository.checkinResource(document, '')
        self.commit()

        document = repository.updateResource(document, first_version)
        self.commit()
        self.failIf(repository.isResourceUpToDate(document))

        document = repository.updateResource(document, None)
        self.commit()
        self.failUnless(repository.isResourceUpToDate(document))


    def testIsResourceChanged(self):
        # Test checking whether a versioned resource has changed.
        repository = self.repository
        document = repository.applyVersionControl(self.document1)
        self.commit()
        if self.do_commits:
            self.failIf(repository.isResourceChanged(document))

        document = repository.checkoutResource(document)
        self.commit()
        if self.do_commits:
            self.failIf(repository.isResourceChanged(document))

        document.manage_edit('change 1', '')
        self.commit()
        if self.do_commits:
            self.failUnless(repository.isResourceChanged(document))

        document = repository.checkinResource(document, '')
        self.commit()
        if self.do_commits:
            self.failIf(repository.isResourceChanged(document))


    def testVersionBookkeeping(self):
        # Check the consistency of the version bookkeeping info.
        repository = self.repository

        document = repository.applyVersionControl(self.document1)
        self.commit()

        info = repository.getVersionInfo(document)
        self.failUnless(info.user_id == 'UnitTester')
        self.failUnless(info.status == info.CHECKED_IN)
        self.failUnless(info.sticky == None)
        first_version = info.version_id

        document = repository.checkoutResource(document)
        self.commit()
        info = repository.getVersionInfo(document)
        self.failUnless(info.status == info.CHECKED_OUT)

        document = repository.checkinResource(document, '')
        self.commit()
        info = repository.getVersionInfo(document)
        self.failUnless(info.status == info.CHECKED_IN)

        document = repository.updateResource(document, first_version)
        self.commit()
        info = repository.getVersionInfo(document)
        self.failUnless(info.status == info.CHECKED_IN)
        self.failUnless(info.version_id == first_version)

        branch_name = 'Bug Fix Branch'
        repository.makeActivity(document, branch_name)
        self.commit()
        document = repository.updateResource(document, branch_name)
        self.commit()
        info = repository.getVersionInfo(document)
        self.failUnless(info.sticky == ('B', branch_name))

        document = repository.updateResource(document, 'mainline')
        self.commit()
        info = repository.getVersionInfo(document)
        self.failUnless(info.sticky == None)

        document = repository.checkoutResource(document)
        self.commit()
        info = repository.getVersionInfo(document)
        self.failUnless(info.status == info.CHECKED_OUT)

        document.manage_edit('change 1', '')
        self.commit()

        document = repository.uncheckoutResource(document)
        self.commit()
        info = repository.getVersionInfo(document)
        self.failUnless(info.status == info.CHECKED_IN)


    def testApplyVersionControl(self):
        # Test checking whether a versioned resource is up to date.
        from Products.ZopeVersionControl.Utility import VersionControlError
        repository = self.repository

        document = repository.applyVersionControl(self.document1)
        self.commit()
        self.failUnless(repository.isUnderVersionControl(document))

        # Make sure we can't do it a second time.
        self.failUnlessRaises(VersionControlError,
                              repository.applyVersionControl,
                              document
                              )

        info = repository.getVersionInfo(document)
    
        # Check that the last log entry record is what we expect.
        record = repository.getLogEntries(document)[0]
        self.failUnless(record.version_id == info.version_id)
        self.failUnless(record.user_id == 'UnitTester')
        self.failUnless(record.action == record.ACTION_CHECKIN)
        self.failUnless(record.path == '/folder1/folder2/document1')


    def testCheckoutResource(self):
        # Test checking out a version controlled resource.
        from Products.ZopeVersionControl.Utility import VersionControlError
        repository = self.repository

        document = repository.applyVersionControl(self.document1)
        self.commit()

        info = repository.getVersionInfo(document)
        first_version = info.version_id

        repository.checkoutResource(document)
        self.commit()

        # Make sure you can't checkout a checked-out resource.
        self.failUnlessRaises(VersionControlError,
                              repository.checkoutResource,
                              document
                              )

        # Check that the last log entry record is what we expect.
        record = repository.getLogEntries(document)[0]
        self.failUnless(record.version_id == first_version)
        self.failUnless(record.user_id == 'UnitTester')
        self.failUnless(record.action == record.ACTION_CHECKOUT)
        self.failUnless(record.path == '/folder1/folder2/document1')

        document = repository.checkinResource(document, '')
        self.commit()
        document = repository.updateResource(document, first_version)
        self.commit()

        # Make sure you can't checkout a non-up-to-date resource.
        self.failUnlessRaises(VersionControlError,
                              repository.checkoutResource,
                              document
                              )

        # Check that the last log entry record is what we expect.
        record = repository.getLogEntries(document)[0]
        self.failUnless(record.version_id == first_version)
        self.failUnless(record.user_id == 'UnitTester')
        self.failUnless(record.action == record.ACTION_UPDATE)
        self.failUnless(record.path == '/folder1/folder2/document1')


    def testCheckinResource(self):
        # Test checking in a version controlled resource.
        from Products.ZopeVersionControl.Utility import VersionControlError
        repository = self.repository

        document = repository.applyVersionControl(self.document1)
        self.commit()

        # Make sure you can't checkin a checked-in resource.
        self.failUnlessRaises(VersionControlError,
                              repository.checkinResource,
                              document, ''
                              )

        info = repository.getVersionInfo(document)
        first_version = info.version_id

        repository.checkoutResource(document)
        self.commit()

        document = repository.checkinResource(document, '')
        self.commit()

        # Check that the last log entry record is what we expect.
        record = repository.getLogEntries(document)[0]
        info = repository.getVersionInfo(document)
        self.failUnless(record.version_id == info.version_id)
        self.failUnless(record.user_id == 'UnitTester')
        self.failUnless(record.action == record.ACTION_CHECKIN)
        self.failUnless(record.path == '/folder1/folder2/document1')

        self.failUnlessRaises(VersionControlError,
                              repository.checkinResource,
                              document, ''
                              )

        document = repository.updateResource(document, first_version)
        self.commit()

        self.failUnlessRaises(VersionControlError,
                              repository.checkinResource,
                              document, ''
                              )


    def testUncheckoutResource(self):
        # Test uncheckout of a version controlled resource.
        from Products.ZopeVersionControl.Utility import VersionControlError
        repository = self.repository

        document = repository.applyVersionControl(self.document1)
        self.commit()

        info = repository.getVersionInfo(document)
        first_version = info.version_id

        repository.checkoutResource(document)
        self.commit()

        document.manage_edit('change 1', '')

        document = repository.uncheckoutResource(document)
        self.commit()

        info = repository.getVersionInfo(document)
        self.failUnless(info.status == info.CHECKED_IN)

        # Check that the last log entry record is what we expect.
        record = repository.getLogEntries(document)[0]
        self.failUnless(record.version_id == first_version)
        self.failUnless(record.user_id == 'UnitTester')
        self.failUnless(record.action == record.ACTION_UNCHECKOUT)
        self.failUnless(record.path == '/folder1/folder2/document1')


    def testUpdateResource(self):
        # Test updating a version controlled resource.
        from Products.ZopeVersionControl.Utility import VersionControlError
        repository = self.repository

        document = repository.applyVersionControl(self.document1)
        self.commit()

        info = repository.getVersionInfo(document)
        first_version = info.version_id

        repository.labelResource(document, 'First Version', 1)

        repository.checkoutResource(document)
        self.commit()

        document = repository.checkinResource(document, '')
        self.commit()

        document = repository.updateResource(document, first_version)
        self.commit()
        info = repository.getVersionInfo(document)
        self.failUnless(info.version_id == first_version)

        document = repository.updateResource(document, None)
        self.commit()

        document = repository.updateResource(document, 'First Version')
        self.commit()
        info = repository.getVersionInfo(document)
        self.failUnless(info.version_id == first_version)

        # Check that the last log entry record is what we expect.
        record = repository.getLogEntries(document)[0]
        self.failUnless(record.version_id == first_version)
        self.failUnless(record.user_id == 'UnitTester')
        self.failUnless(record.action == record.ACTION_UPDATE)
        self.failUnless(record.path == '/folder1/folder2/document1')


    def testLabelResource(self):
        # Test labeling a version controlled resource.
        from Products.ZopeVersionControl.Utility import VersionControlError
        repository = self.repository

        document = repository.applyVersionControl(self.document1)
        self.commit()

        info = repository.getVersionInfo(document)
        first_version = info.version_id

        repository.labelResource(document, 'First Version', 1)

        document = repository.checkoutResource(document)
        self.commit()

        self.failUnlessRaises(VersionControlError,
                              repository.labelResource,
                              document, 'First Version', 1
                              )

        document = repository.uncheckoutResource(document)
        self.commit()

        repository.makeActivity(document, 'Activity 1')

        self.failUnlessRaises(VersionControlError,
                              repository.labelResource,
                              document, 'mainline', 1
                              )

        self.failUnlessRaises(VersionControlError,
                              repository.labelResource,
                              document, 'Activity 1', 1
                              )

        document = repository.checkoutResource(document)
        self.commit()

        document = repository.checkinResource(document, '')
        self.commit()

        self.failUnlessRaises(VersionControlError,
                              repository.labelResource,
                              document, 'First Version', 0
                              )

        document = repository.updateResource(document, 'First Version')
        self.commit()
        info = repository.getVersionInfo(document)
        self.failUnless(info.version_id == first_version)


    def testActivityAPI(self):
        from Products.ZopeVersionControl.Utility import VersionControlError

        repository = self.repository
        document = self.document1

        repository.applyVersionControl(document)
        self.commit()

        self.failUnless(repository.isUnderVersionControl(document))
        self.failUnless(repository.isResourceUpToDate(document))
        if self.do_commits:
            self.failIf(repository.isResourceChanged(document))

        info = repository.getVersionInfo(document)
        self.failUnless(info.sticky == None)
        first_version = info.version_id

        activity_name = 'My Big Project'

        repository.makeActivity(document, activity_name)
        self.commit()

        # Make sure we can't do it again for the same activity id.
        self.failUnlessRaises(VersionControlError,
                              repository.makeActivity,
                              document, activity_name
                              )

        document = repository.updateResource(document, activity_name)
        self.commit()

        self.failUnless(repository.isResourceUpToDate(document))
        if self.do_commits:
            self.failIf(repository.isResourceChanged(document))

        info = repository.getVersionInfo(document)
        self.failUnless(info.version_id == first_version)
        self.failUnless(info.sticky == ('B', activity_name))

        repository.checkoutResource(document)
        self.commit()

        document.manage_edit('activity change 1', '')
        self.commit()

        document = repository.checkinResource(document, 'activity change 1')
        self.commit()

        info = repository.getVersionInfo(document)
        self.failUnless(info.sticky == ('B', activity_name))

        for n in range(10):
            activity_name = 'Activity %d' % n

            repository.makeActivity(document, activity_name)
            self.commit()

            info = repository.getVersionInfo(document)
            root_version = info.version_id

            document = repository.updateResource(document, activity_name)
            self.commit()

            self.failUnless(repository.isResourceUpToDate(document))

            info = repository.getVersionInfo(document)
            self.failUnless(info.sticky == ('B', activity_name))
            self.failUnless(info.version_id == root_version)

            repository.checkoutResource(document)
            self.commit()
                
            document.manage_edit('activity change %d' % n, '')
            self.commit()

            document = repository.checkinResource(
                document, 'activity change %d' % n
                )
            self.commit()

            info = repository.getVersionInfo(document)
            self.failUnless(info.sticky == ('B', activity_name))
            self.failIf(info.version_id == root_version)

        document = repository.updateResource(document, root_version)
        self.commit()

        self.failIf(repository.isResourceUpToDate(document))

        document = repository.updateResource(document, first_version)
        self.commit()

#        self.failUnless(repository.isResourceUpToDate(document))




    def testSelectionByDate(self):
        # Test selection of versions by date.
        from Products.ZopeVersionControl.Utility import VersionControlError
        from DateTime.DateTime import DateTime
        import time

        repository = self.repository
        document = repository.applyVersionControl(self.document1)
        self.commit()

        document = repository.checkoutResource(document)
        self.commit()

        document.manage_edit('change 1', '')
        self.commit()

        document = repository.checkinResource(document, 'change 1')
        self.commit()

        repository.labelResource(document, 'change 1')
        self.commit()

        info = repository.getVersionInfo(document)
        first_version = info.version_id

        # Trickery: we'll hack the timestamp of the first version so
        # that we can act like it was created yesterday :)
        history = repository.getVersionHistory(info.history_id)
        version = history.getVersionById(info.version_id)
        orig_time = version.date_created
        new_time = orig_time - 86400.0
        timestamp = int(orig_time / 60.0)
        new_stamp = int(new_time / 60.0)
        version.date_created = new_time
        branch = history._branches['mainline']
        key, val = branch.m_order.items()[0]
        del branch.m_date[timestamp]
        branch.m_date[new_stamp] = key
        self.commit()

        for n in range(10):
            document = repository.checkoutResource(document)
            self.commit()
            change_no = 'change %d' % (n + 2)
            document.manage_edit(change_no, '')
            self.commit()
            document = repository.checkinResource(document, change_no)
            self.commit()
            repository.labelResource(document, change_no)
            self.commit()

        target_time = time.time() - 14400.0
        document = repository.updateResource(document, target_time)
        self.commit()
        info = repository.getVersionInfo(document)
        self.failUnless(info.version_id == first_version)

        # Now do some branching and make sure we backtrack correctly
        # through the branch lineage when doing date selection.
        document = repository.updateResource(document, 'change 5')
        self.commit()

        for n in range(10):
            activity_name = 'Activity %d' % n
            repository.makeActivity(document, activity_name)
            self.commit()
            document = repository.updateResource(document, activity_name)
            self.commit()
            for i in range(10):
                repository.checkoutResource(document)
                self.commit()
                document.manage_edit('activity change %d' % i, '')
                self.commit()
                document = repository.checkinResource(document, '')
                self.commit()

        document = repository.updateResource(document, target_time)
        self.commit()
        info = repository.getVersionInfo(document)
        self.failUnless(info.version_id == first_version)


    def testSelectionByLabel(self):
        # Test labeling and selection of versions using labels.
        from Products.ZopeVersionControl.Utility import VersionControlError

        repository = self.repository
        document = repository.applyVersionControl(self.document1)

        # Ensure that labeling and lookup by label works as expected.
        label_set = []
        for n in range(10):
            change_no = 'change %d' % n
            document = repository.checkoutResource(document)
            document.manage_edit(change_no, '')
            document = repository.checkinResource(document, change_no)
            repository.labelResource(document, change_no)
            info = repository.getVersionInfo(document)
            label_set.append((change_no, info.version_id))

        for label, version_id in label_set:
            document = repository.updateResource(document, label)
            info = repository.getVersionInfo(document)
            self.failUnless(info.version_id == version_id)
            self.failUnless(info.sticky == ('L', label))

        # Ensure that label moving works as expected and that we get an
        # error if we try to reuse a label without forcing a label move.
        document = repository.updateResource(document, 'change 0')
        repository.labelResource(document, 'change 1', force=1)
        document = repository.updateResource(document, 'change 1')
        info = repository.getVersionInfo(document)
        self.failUnless(info.version_id == label_set[0][1])

        self.failUnlessRaises(VersionControlError,
                              repository.labelResource,
                              document, 'change 3'
                              )


    def testGetVersionOfResource(self):
        # Test retrieving specific versions of resources.
        from Products.ZopeVersionControl.Utility import VersionControlError
        repository = self.repository

        document = repository.applyVersionControl(self.document1)
        self.commit()

        info = repository.getVersionInfo(document)
        history_id = info.history_id
        first_version = info.version_id

        repository.labelResource(document, 'First Version')

        for n in range(10):
            repository.checkoutResource(document)
            self.commit()
            document = repository.checkinResource(document, '')
            self.commit()

        # Make sure the "get version of resource" api is working.
        doc_copy = repository.getVersionOfResource(
            info.history_id, first_version
            )
        info = repository.getVersionInfo(doc_copy)
        self.failUnless(info.version_id == first_version)
        self.failUnless(info.sticky == ('V', first_version))
        self.failUnless(document._p_oid != doc_copy._p_oid)
        self.failUnless(document is not doc_copy)

        doc_copy = repository.getVersionOfResource(
            info.history_id, "First Version"
            )
        info = repository.getVersionInfo(doc_copy)
        self.failUnless(info.version_id == first_version)
        self.failUnless(info.sticky == ('L', 'First Version'))
        self.failUnless(document._p_oid != doc_copy._p_oid)
        self.failUnless(document is not doc_copy)


    def testDetectPersistentSubObjectChange(self):
        # Test detection of changes to persistent sub-objects.
        repository = self.repository
        folder2 = self.folder2
        document = self.document1

        # Place a resource w/ persistent subobjects under version control.
        repository.applyVersionControl(folder2)
        get_transaction().commit()

        document1 = getattr(folder2, 'document1')
        document1.manage_edit('spam spam', '')
        get_transaction().commit()

        self.failUnless(repository.isResourceChanged(folder2))


    def testContainerVersioning(self):
        from OFS.DTMLDocument import addDTMLDocument
        # Verify that containers and items are versioned independently.
        repository = self.repository
        folder1 = self.app.folder1
        folder2 = folder1.folder2
        folder1.testattr = 'container_v1'
        folder2.testattr = 'item_v1'

        self.assert_(not repository.isUnderVersionControl(folder1))
        repository.applyVersionControl(folder1)
        folder1 = self.app.folder1
        self.assert_(repository.isUnderVersionControl(folder1))
        self.assert_(not repository.isUnderVersionControl(folder2))
        repository.applyVersionControl(folder2)
        folder2 = folder1.folder2
        self.assert_(repository.isUnderVersionControl(folder2))
        self.assert_(not repository.isUnderVersionControl(folder2.document1))

        # Make the first version of folder1 and check it in.
        repository.checkoutResource(folder1)
        folder1 = self.app.folder1
        repository.checkinResource(folder1)
        folder1 = self.app.folder1
        folder2 = folder1.folder2
        info = repository.getVersionInfo(folder1)
        first_version = info.version_id

        # Change folder1 and check it in again
        repository.checkoutResource(folder1)
        folder1 = self.app.folder1
        folder1.testattr = 'container_v2'
        addDTMLDocument(folder1, 'document3', file='some more text')
        repository.checkinResource(folder1)
        folder1 = self.app.folder1
        folder2 = folder1.folder2

        # Change folder2
        repository.checkoutResource(folder2)
        folder2 = folder1.folder2
        folder2.testattr = 'item_v2'

        # Now revert folder1 and verify that folder2 was not reverted.
        repository.updateResource(folder1, first_version)
        folder1 = self.app.folder1
        folder2 = folder1.folder2
        self.assertEqual(folder1.testattr, 'container_v1')
        self.assertEqual(folder2.testattr, 'item_v2')

        # Verify that document3 remains an item of the reverted folder1.
        self.assert_(hasattr(folder1, 'document3'))
        self.assert_(str(folder1.document3) == 'some more text')

        # Remove document3 and verify that it doesn't reappear upon revert.
        folder1._delObject('document3')
        repository.updateResource(folder1, '')
        folder1 = self.app.folder1
        self.assertEqual(folder1.testattr, 'container_v2')
        self.assertEqual(folder1.folder2.testattr, 'item_v2')
        self.assert_(not hasattr(folder1, 'document3'))


    def testNonVersionedAttribute(self):
        # Test a non-version-controlled attribute mixed with
        # a version-controlled attribute.
        self.document1.extra_attr = 'v1'
        self.document1.__vc_ignore__ = ('__ac_local_roles__',)
        self.document1.__ac_local_roles__ = {'sam': ['Manager',]}
        repository = self.repository
        document = repository.applyVersionControl(self.document1)
        info = repository.getVersionInfo(document)
        first_version = info.version_id
        repository.checkoutResource(document)
        self.document1.extra_attr = 'v2'
        self.document1.__ac_local_roles__ = {}
        repository.checkinResource(document)
        repository.updateResource(document, first_version)
        self.assertEqual(document.extra_attr, 'v1')
        self.assertEqual(document.__ac_local_roles__, {})

    def testNonVersionedAttributeWithAcquisition(self):
        # Test a non-version-controlled attribute 
        # that is acquired does not cause an error
        self.document1.__vc_ignore__ = ('dummy_attr',)
        self.folder1.dummy_attr = 'dummy_attr'
        self.assertEqual( self.folder1.dummy_attr, self.document1.dummy_attr )

        repository = self.repository
        document = repository.applyVersionControl(self.document1)
        info = repository.getVersionInfo(document)
        first_version = info.version_id
        repository.checkoutResource(document)
        self.document1.extra_attr = 'new'
        repository.checkinResource(document)
        repository.updateResource(document, first_version)

class VersionControlTestsWithCommits(VersionControlTests):
    """Version control test suite with transaction commits that mimic
       the transaction commits that you would get with Web based usage."""
    do_commits = 1

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(VersionControlTests))
    suite.addTest(unittest.makeSuite(VersionControlTestsWithCommits))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')


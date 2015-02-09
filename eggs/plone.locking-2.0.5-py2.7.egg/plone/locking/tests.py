import doctest
import unittest

from DateTime.DateTime import DateTime
from Products.CMFCore.utils import getToolByName

from plone.app.testing.bbb import PTC_FUNCTIONAL_TESTING
from plone.testing import layered

OPTIONFLAGS = (doctest.REPORT_ONLY_FIRST_FAILURE |
               doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE)


def addMember(portal, username, fullname="", email="", roles=('Member', ), last_login_time=None):
    portal_membership = getToolByName(portal, 'portal_membership')
    portal_membership.addMember(username, 'secret', roles, [])
    member = portal_membership.getMemberById(username)
    member.setMemberProperties({'fullname': fullname, 'email': email,
                                'last_login_time': DateTime(last_login_time), })


def setUp(self):
    addMember(self, 'member1', 'Member one')
    addMember(self, 'member2', 'Member two')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(
        layered(doctest.DocFileSuite('README.txt',
                      optionflags=OPTIONFLAGS,
                      package='plone.locking',
                      globs={'addMember': addMember}),
                layer=PTC_FUNCTIONAL_TESTING))
    return suite

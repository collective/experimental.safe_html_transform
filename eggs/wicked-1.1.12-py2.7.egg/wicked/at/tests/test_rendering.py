import os, sys, time
import unittest
from sets import Set
import traceback

from Testing import ZopeTestCase
from wickedtestcase import WickedTestCase, makeContent
from wicked.normalize import titleToNormalizedId
from wicked.config import BACKLINK_RELATIONSHIP

stx_body = """
Here is some structured text data:

- with

- a

- bulleted

- list
"""

class TestWickedRendering(WickedTestCase):
    # an untest?
    wicked_type = 'IronicWiki'
    wicked_field = 'body'

    def test_stxRendering(self):
        self.set_text(self.page1, stx_body, mimetype='text/structured')
        self.failUnless('<ul>' in self.page1.getBody())

def test_suite():
    from wicked.at.link import test_suite as doctests
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestWickedRendering))
    suite.addTest(doctests())
    return suite


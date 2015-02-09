##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import doctest
import re
import unittest

import zc.buildout.testing
import zope.testing.doctest
import zope.testing.renormalizing


def setUp(test):
    zc.buildout.testing.buildoutSetUp(test)
    zc.buildout.testing.install_develop('zc.recipe.testrunner', test)
    zc.buildout.testing.install_develop('zc.recipe.egg', test)
    zc.buildout.testing.install('zope.testing <3.10.0', test)
    zc.buildout.testing.install('zope.exceptions', test)
    zc.buildout.testing.install('zope.interface', test)

def test_suite():
    return unittest.TestSuite((
        zope.testing.doctest.DocFileSuite(
            'README.txt',
            'bugfixes.txt',
            setUp=setUp, tearDown=zc.buildout.testing.buildoutTearDown,
            checker=zope.testing.renormalizing.RENormalizing(
                    [zc.buildout.testing.normalize_path,
                     zc.buildout.testing.normalize_script,
                     zc.buildout.testing.normalize_egg_py,
                     zc.buildout.testing.normalize_endings,
                     (re.compile('#!\S+py\S*'), '#!python'),
                     (re.compile('\d[.]\d+ seconds'), '0.001 seconds'),
                     (re.compile('zope.testing-[^-]+-'), 'zope.testing-X-'),
                     (re.compile('setuptools-[^-]+-'), 'setuptools-X-'),
                     (re.compile('zope.interface-[^-]+-'), 'zope.interface-X-'),
                     (re.compile('zope.exceptions-[^-]+-'), 'zope.exceptions-X-'),
                     #windows happiness for ``extra-paths``:
                     (re.compile(r'[a-zA-Z]:\\\\usr\\\\local\\\\zope\\\\lib\\\\python'),
                                '/usr/local/zope/lib/python'),
                     #windows happiness for ``working-directory``:
                     (re.compile(r'[a-zA-Z]:\\\\foo\\\\bar'),
                                '/foo/bar'),
                     #more windows happiness:
                     (re.compile(r'eggs\\\\'),
                                'eggs/'),
                     (re.compile(r'parts\\\\'),
                                'parts/'),
                     ]),
            ),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

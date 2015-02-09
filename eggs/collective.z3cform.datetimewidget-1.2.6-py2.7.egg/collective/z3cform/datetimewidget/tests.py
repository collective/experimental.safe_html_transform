#-*- coding: utf-8 -*- 

#############################################################################
#                                                                           #
#   Copyright (c) 2008 Rok Garbas <rok@garbas.si>                           #
#                                                                           #
# This program is free software; you can redistribute it and/or modify      #
# it under the terms of the GNU General Public License as published by      #
# the Free Software Foundation; either version 3 of the License, or         #
# (at your option) any later version.                                       #
#                                                                           #
# This program is distributed in the hope that it will be useful,           #
# but WITHOUT ANY WARRANTY; without even the implied warranty of            #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
# GNU General Public License for more details.                              #
#                                                                           #
# You should have received a copy of the GNU General Public License         #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.     #
#                                                                           #
#############################################################################
__docformat__ = "reStructuredText"

import doctest
import unittest
import zope.component.testing
from zope.interface import implements
from zope.publisher.browser import TestRequest
from z3c.form.interfaces import IFieldWidget
from z3c.form.interfaces import IFormLayer

from Testing import ZopeTestCase as ztc
from StringIO import StringIO
import z3c.form
import zope.component
import zope.publisher
import zope.traversing
import collective.z3cform.datetimewidget
from zope.configuration import xmlconfig


class DummyContext(object):
    pass


class TestRequest(TestRequest):
    implements(IFormLayer)


class WidgetTestCase(object):

    def setUp(self):
        self.root = DummyContext()
        zope.component.testing.setUp()
        xmlconfig.XMLConfig('meta.zcml', zope.component)()
        xmlconfig.XMLConfig('configure.zcml', zope.traversing)()
        xmlconfig.XMLConfig('configure.zcml', zope.publisher)()
        try:
            xmlconfig.XMLConfig('configure.zcml', zope.i18n)()
        except IOError:
            # Zope 2.10
            xmlconfig.xmlconfig(StringIO('''
            <configure xmlns="http://namespaces.zope.org/zope">
               <utility
                  provides="zope.i18n.interfaces.INegotiator"
                  component="zope.i18n.negotiator.negotiator" />

               <include package="zope.i18n.locales" />
            </configure>
             '''))
        xmlconfig.XMLConfig('meta.zcml', zope.i18n)()
        xmlconfig.XMLConfig('meta.zcml', z3c.form)()
        xmlconfig.XMLConfig('configure.zcml', collective.z3cform.datetimewidget)()

    def tearDown(self):
        zope.component.testing.tearDown()

    def testrequest(self, lang="en", form={}):
        return TestRequest(HTTP_ACCEPT_LANGUAGE=lang, form=form)

    def setupWidget(self, field, lang="en"):
        request = self.testrequest(lang=lang)
        widget = zope.component.getMultiAdapter((field, request),
                                                IFieldWidget)
        widget.id = 'foo'
        widget.name = 'bar'
        return widget


def test_suite():
    return unittest.TestSuite((
        ztc.ZopeDocFileSuite(
            'widget_date.txt',
            'widget_datetime.txt',
            'widget_monthyear.txt',
            'converter.txt',
            'issues.txt',
            test_class=WidgetTestCase,
            optionflags=
                        doctest.NORMALIZE_WHITESPACE |
                        doctest.ELLIPSIS |
                        doctest.REPORT_UDIFF,
            ),
        ))


# -*- coding: utf-8 -*-

import unittest2 as unittest

from zope.component import getMultiAdapter

from archetypes.querywidget.tests.base import QUERYWIDGET_INTEGRATION_TESTING


class BrowserLayerTest(unittest.TestCase):

    layer = QUERYWIDGET_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']

    def test_sorted_values(self):
        view = getMultiAdapter((
            self.portal.collection, self.request),
            name="archetypes-querywidget-selectionwidget")

        string_values = view.getValues(index='string')
        integer_values = view.getValues(index='integer')

        self.assertEqual(view.getSortedValuesKeys(string_values), ['a', 'b', 'c'])
        self.assertEqual(view.getSortedValuesKeys(integer_values), [1, 2, 3])

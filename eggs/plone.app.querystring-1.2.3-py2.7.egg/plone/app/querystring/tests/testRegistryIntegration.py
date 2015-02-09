from plone.app.querystring.testing import PLONEAPPQUERYSTRING_INTEGRATION_TESTING

import unittest2 as unittest


class TestOperationDefinitions(unittest.TestCase):

    layer = PLONEAPPQUERYSTRING_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']

    def test_string_equality(self):
        registry = self.portal.portal_registry

        prefix = "plone.app.querystring.operation.string.is"
        self.assertTrue(prefix + '.title' in registry)

        self.assertEqual(registry[prefix + ".title"], "Is")
        self.assertEqual(registry[prefix + ".description"],
                         'Tip: you can use * to autocomplete.')
        self.assertEqual(registry[prefix + ".operation"],
                         u'plone.app.querystring.queryparser._equal')

    def test_date_lessthan(self):
        registry = self.portal.portal_registry
        prefix = 'plone.app.querystring.operation.date.lessThan'

        self.assertTrue(prefix + ".title" in registry)

        self.assertEqual(registry[prefix + ".title"], "Before date")
        self.assertEqual(registry[prefix + ".description"],
                         'Please use YYYY/MM/DD.')
        self.assertEqual(registry[prefix + ".operation"],
                         u'plone.app.querystring.queryparser._lessThan')


class TestFieldDefinitions(unittest.TestCase):

    layer = PLONEAPPQUERYSTRING_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']

    def test_getId(self):
        registry = self.portal.portal_registry
        prefix = 'plone.app.querystring.field.getId'
        self.assertTrue(prefix + ".title" in registry)

        self.assertEqual(registry[prefix + ".title"], "Short name (id)")

        operations = registry[prefix + ".operations"]
        self.assertEqual(len(operations), 1)

        equal = 'plone.app.querystring.operation.string.is'
        self.assertTrue(equal in operations)

        self.assertEqual(registry[prefix + ".description"],
                         "The short name of an item (used in the url)")
        self.assertEqual(registry[prefix + ".enabled"], True)
        self.assertEqual(registry[prefix + ".sortable"], True)
        self.assertEqual(registry[prefix + ".group"], "Metadata")

    def test_getobjpositioninparent_largerthan(self):
        """Bug reported as Issue #22

        Names not matching for operations getObjPositionInParent
        see also https://github.com/plone/plone.app.querystring/issues/22
        """
        key = 'plone.app.querystring.field.getObjPositionInParent.operations'
        operation = 'plone.app.querystring.operation.int.largerThan'
        registry = self.portal.portal_registry

        # check if operation is used for getObjPositionInParent
        operations = registry.get(key)
        self.assertTrue(operation in operations)

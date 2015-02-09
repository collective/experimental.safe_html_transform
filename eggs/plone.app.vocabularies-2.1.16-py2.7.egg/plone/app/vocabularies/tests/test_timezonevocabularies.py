from plone.app.vocabularies.testing import PAVocabularies_INTEGRATION_TESTING
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

import unittest2 as unittest


class TimezoneTest(unittest.TestCase):
    layer = PAVocabularies_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']

    def test_timezone_vocabulary(self):
        tzvocab = getUtility(IVocabularyFactory, 'plone.app.vocabularies.Timezones')
        tz_list = [item.value for item in tzvocab(self.portal)]
        self.assertTrue('Africa/Abidjan' in tz_list)
        self.assertTrue('Europe/London' in tz_list)

    def test_timezone_vocabulary_query(self):
        tzvocab = getUtility(IVocabularyFactory, 'plone.app.vocabularies.Timezones')
        tz_list = [item.value for item in tzvocab(self.portal, query='vienna')]
        self.assertTrue('Europe/Vienna' in tz_list)
        self.assertTrue(len(tz_list) == 1)

    def test_available_timezones_vocabulary(self):
        reg = getUtility(IRegistry)
        # check if "plone.available_timezones" available_timezones' in registry
        reg_key = 'plone.available_timezones'
        if reg_key not in reg:
            # ignore for Plone 4.3 w/o plone.app.event available
            return

        # this works only for plone.app.event 2.0
        # initially, all common zones are available in AvailableTimezones
        common_zones_vocab = getUtility(
            IVocabularyFactory,
            'plone.app.vocabularies.CommonTimezones'
        )(self.portal)
        avail_zones_vocab = getUtility(
            IVocabularyFactory,
            'plone.app.vocabularies.AvailableTimezones'
        )(self.portal)
        self.assertTrue(len(common_zones_vocab) > len(avail_zones_vocab) > 0)

        # let's limit it to the first 10 zones of all_zones
        common_zones = [term.value for term in common_zones_vocab]
        reg[reg_key] = common_zones[0:10]

        # the AvailableTimezones vocabulary must instantiated again, to reflect
        # those changes
        del avail_zones_vocab
        avail_zones_vocab = getUtility(
            IVocabularyFactory,
            'plone.app.vocabularies.AvailableTimezones'
        )(self.portal)

        # the length of the avail_zones_vocab is now 10
        self.assertTrue(len(common_zones_vocab) > len(avail_zones_vocab) > 0)
        self.assertEqual(len(avail_zones_vocab), 10)

        # Test querying AvailableTimezones vocabulary
        reg[reg_key] = common_zones
        filtered_zones_vocab = getUtility(
            IVocabularyFactory,
            'plone.app.vocabularies.AvailableTimezones'
        )(self.portal, query='vienna')
        # filtered all items down to one
        self.assertEqual(len(filtered_zones_vocab), 1)

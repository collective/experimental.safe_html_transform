from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.i18nmessageid import MessageFactory
from zope.interface import provider
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

import pytz

PLMF = MessageFactory('plonelocales')


@provider(IVocabularyFactory)
def TimezonesFactory(context, query=None):
    """Vocabulary for all timezones.

    This are all timezones supported by pytz.
    """
    tz_list = [SimpleTerm(value=it, title=PLMF(it, default=it))
               for it in pytz.all_timezones
               if query is None or query.lower() in it.lower()]
    return SimpleVocabulary(tz_list)


@provider(IVocabularyFactory)
def CommonTimezonesFactory(context, query=None):
    """Vocabulary for common timezones.

    This are the timezones a user would choose from in a form.
    """
    tz_list = [SimpleTerm(value=it, title=PLMF(it, default=it))
               for it in pytz.common_timezones
               if query is None or query.lower() in it.lower()]
    return SimpleVocabulary(tz_list)


@provider(IVocabularyFactory)
def AvailableTimezonesFactory(context, query=None):
    """Vocabulary for available timezones, as set by in the controlpanel.
    """
    reg_key = "plone.available_timezones"
    registry = getUtility(IRegistry)
    # check if 'plone.available_timezones' is in registry
    if reg_key not in registry:
        # else use 'plone.app.event.available_timezones'
        reg_key = 'plone.app.event.available_timezones'
    if reg_key not in registry:
        raise NotImplementedError(
            '"available timezones" needs Plone 5.x or plone.app.event '
            'installed.'
        )
    tz_list = [SimpleTerm(value=it, title=PLMF(it, default=it))
               for it in registry[reg_key]
               if query is None or query.lower() in it.lower()]
    return SimpleVocabulary(tz_list)


# PLEASE NOTE: strftime %w interprets 0 as Sunday unlike the calendar module!
WEEKDAY_PREFIXES = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']


@provider(IVocabularyFactory)
def WeekdaysFactory(context):
    """Vocabulary for Weekdays - full name

      >>> from zope.component import queryUtility
      >>> from plone.app.vocabularies.tests.base import create_context

      >>> name = 'plone.app.vocabularies.Weekdays'
      >>> util = queryUtility(IVocabularyFactory, name)
      >>> context = create_context()

      >>> len(util(context))
      7

      >>> util(context).by_token['0'].title
      u'weekday_mon'
    """
    items = []
    for idx in range(len(WEEKDAY_PREFIXES)):
        msgstr = PLMF('weekday_{0}'.format(WEEKDAY_PREFIXES[idx]))
        items.append(SimpleTerm(idx, str(idx), msgstr))
    return SimpleVocabulary(items)


@provider(IVocabularyFactory)
def WeekdaysAbbrFactory(context):
    """Vocabulary for Weekdays - abbreviated (3 char)

      >>> from zope.component import queryUtility
      >>> from plone.app.vocabularies.tests.base import create_context

      >>> name = 'plone.app.vocabularies.WeekdaysAbbr'
      >>> util = queryUtility(IVocabularyFactory, name)
      >>> context = create_context()

      >>> len(util(context))
      7
    """
    items = []
    for idx in range(len(WEEKDAY_PREFIXES)):
        msgstr = PLMF('weekday_{0}_abbr'.format(WEEKDAY_PREFIXES[idx]))
        items.append(SimpleTerm(idx, str(idx), msgstr))
    return SimpleVocabulary(items)


@provider(IVocabularyFactory)
def WeekdaysShortFactory(context):
    """Vocabulary for Weekdays - Short (2 char)

      >>> from zope.component import queryUtility
      >>> from plone.app.vocabularies.tests.base import create_context

      >>> name = 'plone.app.vocabularies.WeekdaysShort'
      >>> util = queryUtility(IVocabularyFactory, name)
      >>> context = create_context()

      >>> len(util(context))
      7
    """
    items = []
    for idx in range(len(WEEKDAY_PREFIXES)):
        msgstr = PLMF('weekday_{0}_short'.format(WEEKDAY_PREFIXES[idx]))
        items.append(SimpleTerm(idx, str(idx), msgstr))
    return SimpleVocabulary(items)


MONTH_PREFIXES = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                  'jul', 'aug', 'sep', 'oct', 'nov', 'dec']


@provider(IVocabularyFactory)
def MonthFactory(context):
    """Vocabulary for Month. Full name

      >>> from zope.component import queryUtility
      >>> from plone.app.vocabularies.tests.base import create_context

      >>> name = 'plone.app.vocabularies.Month'
      >>> util = queryUtility(IVocabularyFactory, name)
      >>> context = create_context()

      >>> len(util(context))
      12
    """
    items = []
    for idx in range(len(MONTH_PREFIXES)):
        msgstr = PLMF('month_{0}'.format(MONTH_PREFIXES[idx]))
        items.append(SimpleTerm(idx, str(idx), msgstr))
    return SimpleVocabulary(items)


@provider(IVocabularyFactory)
def MonthAbbrFactory(context):
    """Vocabulary for Month. Abbreviated Name (3 char)

      >>> from zope.component import queryUtility
      >>> from plone.app.vocabularies.tests.base import create_context

      >>> name = 'plone.app.vocabularies.MonthAbbr'
      >>> util = queryUtility(IVocabularyFactory, name)
      >>> context = create_context()

      >>> len(util(context))
      12
    """
    items = []
    for idx in range(len(MONTH_PREFIXES)):
        msgstr = PLMF('month_{0}_abbr'.format(MONTH_PREFIXES[idx]))
        items.append(SimpleTerm(idx, str(idx), msgstr))
    return SimpleVocabulary(items)

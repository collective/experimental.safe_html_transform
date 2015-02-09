from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from plone.app.querystring.interfaces import IQuerystringRegistryReader
from zope.publisher.browser import BrowserView


def sortable_value(value):
    if isinstance(value, basestring):
        value = value.lower()
    return value


class datepickerconfig(BrowserView):

    calendar_type = 'gregorian'

    def __call__(self):
        language = getattr(self.request, 'LANGUAGE', 'en')
        calendar = self.request.locale.dates.calendars[self.calendar_type]

        template = """
jQuery.tools.dateinput.localize("%(language)s", {
    months: "%(monthnames)s",
    shortMonths: "%(shortmonths)s",
    days: "%(days)s",
    shortDays: "%(shortdays)s"
});

jQuery.tools.dateinput.conf.lang = "%(language)s";
jQuery.tools.dateinput.conf.format = "mm/dd/yyyy";
        """
        self.request.response.setHeader(
            'Content-Type', 'application/javascript; charset=utf-8')

        return template % (dict(language=language,
                                monthnames=','.join(calendar.getMonthNames()),
                                shortmonths=','.join(calendar.getMonthAbbreviations()),
                                days=','.join(calendar.getDayNames()),
                                shortdays=','.join(calendar.getDayAbbreviations()),
                                format=format
                                ))


class WidgetTraverse(BrowserView):

    def getConfig(self):
        """get the config"""
        registry = getUtility(IRegistry)
        registryreader = IQuerystringRegistryReader(registry)
        config = registryreader()

        # Group indices by "group", order alphabetically
        groupedIndexes = {}
        for indexName in config['indexes']:
            index = config['indexes'][indexName]
            if index['enabled']:
                group = index['group']
                if group not in groupedIndexes:
                    groupedIndexes[group] = []
                groupedIndexes[group].append((index['title'], indexName))

        # Sort each index list
        [a.sort() for a in groupedIndexes.values()]

        config['groupedIndexes'] = groupedIndexes
        return config

    @property
    def macros(self):
        return self.index.macros


class MultiSelectWidget(WidgetTraverse):

    def getValues(self, index=None):
        config = self.getConfig()
        if not index:
            index = self.request.form.get('index')
        values = None
        if index is not None:
            values = config['indexes'][index]['values']
        return values

    def getSortedValuesKeys(self, values):
        # do a lowercase sort of the keys
        return sorted(values.iterkeys(), key=sortable_value)


class SelectWidget(MultiSelectWidget):

    def getValues(self, index=None):
        config = self.getConfig()
        if not index:
            index = self.request.form.get('index')
        values = None
        if index is not None:
            values = config['indexes'][index]['values']
        return values

    def getSortedValuesKeys(self, values):
        # do a lowercase sort of the keys
        return sorted(values.iterkeys(), key=sortable_value)

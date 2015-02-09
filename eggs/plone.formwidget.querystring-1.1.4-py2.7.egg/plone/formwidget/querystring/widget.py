from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile
from zope.component import getUtility
from zope.component import getMultiAdapter
from zope.interface import implements, implementer
from zope.site.hooks import getSite
import z3c.form.interfaces
import z3c.form.util
from z3c.form.widget import FieldWidget
from z3c.form.widget import Widget
from plone.app.querystring.querybuilder import QueryBuilder
from plone.app.querystring.interfaces import IQuerystringRegistryReader
from plone.formwidget.querystring.interfaces import IQueryStringWidget
from plone.registry.interfaces import IRegistry


class QueryStringWidget(Widget):
    implements(IQueryStringWidget)

    calendar_type = 'gregorian'
    klass = u'querystring-widget'
    input_template = ViewPageTemplateFile('input.pt')

    def render(self):
        return self.input_template(self)

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

    def SearchResults(self):
        """Search results"""
        site = getSite()
        options = dict(original_context=site)
        querybuilder = QueryBuilder(site, self.request)
        listing = querybuilder(query=self.value)
        return getMultiAdapter((listing, self.request),
            name='display_query_results')(**options)


    def js(self):
        language = getattr(self.request, 'LANGUAGE', 'en')
        calendar = self.request.locale.dates.calendars[self.calendar_type]
        localize =  'jQuery.tools.dateinput.localize("' + language + '", {'
        localize += 'months: "%s",' % ','.join(calendar.getMonthNames())
        localize += 'shortMonths: "%s",' % ','.join(calendar.getMonthAbbreviations())
        # calendar tool's number of days is off by one from jquery tools'
        localize += 'days: "%s",' % ','.join(
            [calendar.getDayNames()[6]] + calendar.getDayNames()[:6])
        localize += 'shortDays: "%s"' % ','.join(
            [calendar.getDayAbbreviations()[6]] +
            calendar.getDayAbbreviations()[:6])
        localize += '});'

        defaultlang = 'jQuery.tools.dateinput.conf.lang = "%s";' % language

        return '''
            <script type="text/javascript">
                jQuery(document).ready(function() {
                    if (jQuery().dateinput) {
                        %(localize)s
                        %(defaultlang)s
                    }
                });
            </script>''' % dict(defaultlang=defaultlang, localize=localize)


@implementer(z3c.form.interfaces.IFieldWidget)
def QueryStringFieldWidget(field, request):
    return FieldWidget(field, QueryStringWidget(request))

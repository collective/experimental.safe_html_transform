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

import zope.i18n
import zope.schema
import zope.interface
import zope.component
import z3c.form
import z3c.form.browser.widget
import z3c.form.widget
from datetime import date, datetime
from interfaces import IDateWidget
from i18n import MessageFactory as _
from Products.CMFCore.utils import getToolByName


class DateWidget(z3c.form.browser.widget.HTMLTextInputWidget,
                 z3c.form.widget.Widget):
    """ Date widget. """

    zope.interface.implementsOnly(IDateWidget)

    calendar_type = 'gregorian'
    klass = u'date-widget'
    value = ('', '', '')


    #
    # pure javascript no dependencies
    show_today_link = False

    #
    # Requires: jquery.tools.datewidget.js, jquery.js
    # Read more: http://flowplayer.org/tools/dateinput/index.html
    show_jquerytools_dateinput = False
    jquerytools_dateinput_config = 'selectors: true, trigger: true, '
    yearRange = 'yearRange: [-10, 10]'

    # TODO: implement same thing for JQuery.UI

    def _set_yearRange(self):
        """Set the value of the yearRange configuration variable using the
        min/max field properties or the default values stored in portal's site
        properties.
        """
        portal_properties = getToolByName(self.context, 'portal_properties', None)
        if portal_properties is not None:
            p = portal_properties['site_properties']
        else:
            p = None
        today = date.today()

        if self.field.min is not None:
            start = self.field.min.year - today.year
        else:
            calendar_starting_year = getattr(p, 'calendar_starting_year', 2001)
            start = calendar_starting_year - today.year

        if self.field.max is not None:
            end = self.field.max.year - today.year
        else:
            end = getattr(p, 'calendar_future_years_available', 5)

        self.yearRange = 'yearRange: [%s, %s]' % (start, end)

    def update(self):
        super(DateWidget, self).update()
        z3c.form.browser.widget.addFieldClass(self)
        self._set_yearRange()

    @property
    def months(self):
        try:
            selected = int(self.month)
        except:
            selected = -1

        calendar = self.request.locale.dates.calendars[self.calendar_type]
        month_names = calendar.getMonthNames()

        for i, month in enumerate(month_names):
            yield dict(
                name     = month,
                value    = i+1,
                selected = i+1 == selected)

    @property
    def formatted_value(self):
        try:
            date_value = date(*map(int, self.value))
        except ValueError:
            return ''
        formatter = self.request.locale.dates.getFormatter("date", "short")
        if date_value.year > 1900:
            return formatter.format(date_value)
        # due to fantastic datetime.strftime we need this hack
        # for now ctime is default
        return date_value.ctime()

    @property
    def year(self):
        year = self.request.get(self.name+'-year', None)
        if year is not None:
            return year
        return self.value[0]

    @property
    def month(self):
        month = self.request.get(self.name+'-month', None)
        if month:
            return month
        return self.value[1]

    @property
    def day(self):
        day = self.request.get(self.name+'-day', None)
        if day is not None:
            return day
        return self.value[2]

    def extract(self, default=z3c.form.interfaces.NOVALUE):
        # get normal input fields
        day = self.request.get(self.name + '-day', default)
        month = self.request.get(self.name + '-month', default)
        year = self.request.get(self.name + '-year', default)

        if not default in (year, month, day):
            return (year, month, day)

        # get a hidden value
        formatter = self.request.locale.dates.getFormatter("date", "short")
        hidden_date = self.request.get(self.name, '')
        try:
            dateobj = formatter.parse(hidden_date)
            return (str(dateobj.year),
                    str(dateobj.month),
                    str(dateobj.day))
        except zope.i18n.format.DateTimeParseError:
            pass

        return default

    def show_today_link_js(self):
        now = datetime.today()
        show_link_func = self.id+'-show-today-link'
        for i in ['-', '_']:
            show_link_func = show_link_func.replace(i, '')
        return ' <a href="#" onclick="' \
            'document.getElementById(\'%(id)s-day\').value = %(day)s;' \
            'document.getElementById(\'%(id)s-month\').value = %(month)s;' \
            'document.getElementById(\'%(id)s-year\').value = %(year)s;' \
            'return false;">%(today)s</a>' % dict(
                id = self.id,
                day = now.day,
                month = now.month,
                year = now.year,
                today = zope.i18n.translate(_(u"Today"), context=self.request)
            )

    def show_jquerytools_dateinput_js(self):
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

        config = 'lang: "%s", ' % language

        value_date = self.value[:3]
        if '' not in value_date:
            config += 'value: new Date("%s/%s/%s"), ' % (value_date)

        config += 'change: function() { ' \
                    'var value = this.getValue("yyyy-m-dd").split("-"); \n' \
                    'jQuery("#%(id)s-year").val(value[0]); \n' \
                    'jQuery("#%(id)s-month").val(value[1]); \n' \
                    'jQuery("#%(id)s-day").val(value[2]); \n' \
                '}, ' % dict(id = self.id)
        config += 'firstDay: %s,' % (calendar.week['firstDay'] % 7)
        config += self.jquerytools_dateinput_config
        config += self.yearRange

        return '''
            <input type="hidden" name="%(name)s-calendar"
                   id="%(id)s-calendar" />
            <script type="text/javascript">
                jQuery(document).ready(function() {
                    if (jQuery().dateinput) {
                        %(localize)s
                        jQuery("#%(id)s-calendar").dateinput({%(config)s}).unbind('change')
                            .bind('onShow', function (event) {
                                var trigger_offset = jQuery(this).next().offset();
                                jQuery(this).data('dateinput').getCalendar().offset(
                                    {top: trigger_offset.top+20, left: trigger_offset.left}
                                );
                            });
                    }
                });
            </script>''' % dict(
                id=self.id, name=self.name,
                day=self.day, month=self.month, year=self.year,
                config=config, language=language, localize=localize,
            )

@zope.component.adapter(zope.schema.interfaces.IField, z3c.form.interfaces.IFormLayer)
@zope.interface.implementer(z3c.form.interfaces.IFieldWidget)
def DateFieldWidget(field, request):
    """IFieldWidget factory for DateWidget."""
    return z3c.form.widget.FieldWidget(field, DateWidget(request))



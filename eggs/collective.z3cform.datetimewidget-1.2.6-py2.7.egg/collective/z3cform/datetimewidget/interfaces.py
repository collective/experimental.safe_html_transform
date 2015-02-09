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


import z3c.form
import z3c.form.interfaces
import zope.schema

from i18n import MessageFactory as _


# Fields

class IDateField(zope.schema.interfaces.IDate):
    """ Special marker for date fields that use our widget """


class IDatetimeField(zope.schema.interfaces.IDatetime):
    """ Special marker for datetime fields that use our widget """


# Widgets

class IDateWidget(z3c.form.interfaces.IWidget):
    """ Date widget marker for z3c.form """

    show_today_link = zope.schema.Bool(
        title=u'Show "today" link',
        description=(u'show a link that uses javascript to inserts '
                     u'the current date into the widget.'),
        default=False,
        )


class IDatetimeWidget(z3c.form.interfaces.IWidget):
    """ Datetime widget marker for z3c.form """


class IMonthYearWidget(z3c.form.interfaces.IWidget):
    """ MonthYear widget marker for z3c.form """


# Errors

class DateValidationError(zope.schema.ValidationError, ValueError):
    __doc__ = _(u'Please enter a valid date.')


class DatetimeValidationError(zope.schema.ValidationError, ValueError):
    __doc__ = _(u'Please enter a valid date and time.')

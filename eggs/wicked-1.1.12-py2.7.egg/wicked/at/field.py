##########################################################
#
# Licensed under the terms of the GNU Public License
# (see docs/LICENSE.GPL)
#
# Copyright (c) 2005:
#   - The Open Planning Project (http://www.openplans.org/)
#   - Whit Morriss <whit@kalistra.com>
#   - Rob Miller <rob@kalistra.com> (RaFromBRC)
#   - and contributors
#
##########################################################
from Products.Archetypes import public as atapi
from Products.Archetypes.Registry import registerField
from Products.Archetypes.interfaces import IBaseObject
from ZPublisher.HTTPRequest import FileUpload
from wicked import utils
from wicked.fieldevent.interfaces import IFieldRenderEvent, IFieldStorageEvent
from wicked.fieldevent.interfaces import ITxtFilterList, IFieldValueSetter
from wicked.interfaces import IAmWicked, IAmWickedField, IValueToString
from wicked.txtfilter import WickedFilter
from zope.component import adapter, adapts
from zope.interface import implements, implementer
from wicked.at.interfaces import IAmATWickedField
from cStringIO import StringIO

class WikiField(atapi.TextField):
    """ drop-in wiki """
    implements(IAmWickedField)

    _properties = atapi.TextField._properties.copy()
    _properties.update({
        'scope': '',
        })

registerField(WikiField,
              title='Wiki',
              description='Text field capable of wiki style behavior')


@implementer(IValueToString)
@adapter(atapi.BaseUnit, IAmATWickedField)
def baseunit_to_string(value, field):
    """this avoid a security proxy that will foul regexes"""
    return value.getRaw()


@implementer(IValueToString)
@adapter(FileUpload, IAmWickedField)
def fileupload_to_string(value, field):
    """a file was uploaded, get the (possibly transformed) value"""
    # XXX no `instance` defined
    return field.get(instance, skip_filters=True)




import zope.i18nmessageid

MessageFactory = zope.i18nmessageid.MessageFactory('plone.formwidget.namedfile')

from plone.formwidget.namedfile.widget import NamedFileWidget
from plone.formwidget.namedfile.widget import NamedImageWidget

from plone.formwidget.namedfile.widget import NamedFileFieldWidget
from plone.formwidget.namedfile.widget import NamedImageFieldWidget

# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from z3c.form import interfaces
 
from zope import schema
from zope.interface import Interface
 
from zope.i18nmessageid import MessageFactory
 
_ = MessageFactory('experimental.safe_html_transform')
 
 
class IExperimenatalSafe_Html_TransformSettings(Interface):
"""Global safe_html_transform settings. This describes records stored in the
	configuration registry and obtainable via plone.registry.
"""
 
    Experimentalsafe_html_transform_key = schema.TextLine(title=_(u"Experimenatalsafe_html_transform (Wordpress) Key"),
                                  description=_(u"help_Experimentalsafe_html_transform_key",
                                                default=u"Enter in your Wordpress key here to "
                                                         "use Experimentalsafe_html_transform to check for spam in comments."),
                                  required=False,
                                  default=u'',)
 
    Experimentalsafe_html_transform_key_site = schema.TextLine(title=_(u"Site URL"),
                                  description=_(u"help_Experimentalsafe_html_transform_key_site",
                                                default=u"Enter the URL to this site as per your "
                                                         "Experimentalsafe_html_transform settings."),
                                  required=False,
                                  default=u'',)


class IExperimentalSafeHtmlTransformLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""

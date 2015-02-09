from zope.i18nmessageid import MessageFactory
from Products.CMFCore.permissions import setDefaultRoles

PloneMessageFactory = MessageFactory('plone')

setDefaultRoles('plone.portlet.static: Add static portlet',
                ('Manager', 'Site Administrator', 'Owner', ))

# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from zope.component.hooks import getSite
from plone.app.robotframework.remote import RemoteLibrary


class Users(RemoteLibrary):

    def create_user(self, *args, **kwargs):
        """Create user with given details and return its id"""
        # XXX: Because kwargs are only supported with robotframework >= 2.8.3,
        # we must parse them here to support robotframework < 2.8.3.
        for arg in [x for x in args if '=' in x]:
            name, value = arg.split('=', 1)
            kwargs[name] = value

        assert len(args), u"username must be provided."
        username = args[0]

        roles = []
        properties = kwargs
        for arg in [x for x in args[1:] if not '=' in x]:
            roles.append(arg)
        if not 'email' in properties:
            properties['email'] = '%s@example.com' % username

        portal = getSite()
        registration = getToolByName(portal, 'portal_registration')
        portal_properties = getToolByName(portal, 'portal_properties')

        use_email_as_username =\
            portal_properties.site_properties.use_email_as_login

        user_id = use_email_as_username and properties['email'] or username
        password = properties.pop('password', username)
        roles = properties.pop('roles', ('Member', ))

        properties['username'] = user_id
        registration.addMember(
            user_id, password, roles, properties=properties)

from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.requestmethod import postonly
from App.config import getConfiguration
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PluggableAuthService.interfaces.plugins \
        import IExtractionPlugin, IAuthenticationPlugin, \
                ICredentialsResetPlugin, ICredentialsUpdatePlugin
from Products.PluggableAuthService.permissions import ManageUsers
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.utils import classImplements
from plone.keyring.interfaces import IKeyManager
from plone.session import tktauth
from plone.session.interfaces import ISessionPlugin
from zope.component import getUtility, queryUtility

from email.Utils import formatdate
import binascii
import time

EMPTY_GIF = (
    'GIF89a\x01\x00\x01\x00\xf0\x01\x00\xff\xff\xff'
    '\x00\x00\x00!\xf9\x04\x01\n\x00\x00\x00'
    ',\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
    )

manage_addSessionPluginForm = PageTemplateFile('session', globals())


def manage_addSessionPlugin(dispatcher, id, title=None, path='/',
                            REQUEST=None):
    """Add a session plugin."""
    sp=SessionPlugin(id, title=title, path=path)
    dispatcher._setObject(id, sp)

    if REQUEST is not None:
        REQUEST.response.redirect('%s/manage_workspace?'
                               'manage_tabs_message=Session+plugin+created.' %
                               dispatcher.absolute_url())


def cookie_expiration_date(days):
    expires = time.time() + (days * 24 * 60 * 60)
    return formatdate(expires, usegmt=True)


class SessionPlugin(BasePlugin):
    """Session authentication plugin.
    """

    meta_type = "Plone Session Plugin"
    security = ClassSecurityInfo()

    cookie_name = "__ac"
    cookie_lifetime = 0
    cookie_domain = ''
    mod_auth_tkt = False
    timeout = 12*60*60 # 12h. Default is 2h in mod_auth_tkt
    refresh_interval = 1*60*60 # -1 to disable
    external_ticket_name = 'ticket'
    secure = False
    _shared_secret = None

    # These mod_auth_tkt options are not yet implemented
    #ignoreIP = True # you always want this on the public internet
    #timeoutRefresh = 0 # default is 0.5 in mod_auth_tkt

    _properties = (
            {
                 "id": "timeout",
                 "label": "Cookie validity timeout (in seconds)",
                 "type": "int",
                 "mode": "w",
             },
            {
                 "id": "refresh_interval",
                 "label": "Refresh interval (in seconds, -1 to disable refresh)",
                 "type": "int",
                 "mode": "w",
             },
            {
                 "id": "mod_auth_tkt",
                 "label": "Use mod_auth_tkt compatible hashing algorithm",
                 "type": "boolean",
                 "mode": "w",
             },
            {
                "id": "cookie_name",
                "label": "Cookie name",
                "type": "string",
                "mode": "w",
            },
            {
                "id": "cookie_lifetime",
                "label": "Cookie lifetime (in days)",
                "type": "int",
                "mode": "w",
            },
            {
                 "id": "cookie_domain",
                 "label": "Cookie domain (blank for default)",
                 "type": "string",
                 "mode": "w",
            },
            {
                 "id": "path",
                 "label": "Cookie path",
                 "type": "string",
                 "mode": "w",
            },
            {
                "id": "secure",
                "label": "Only Send Cookie Over HTTPS",
                "type": "boolean",
                "mode": "w",
            },
            )

    manage_options = (
        dict(label='Manage secrets', action='manage_secret'),
        ) + BasePlugin.manage_options

    def __init__(self, id, title=None, path="/"):
        self._setId(id)
        self.title=title
        self.path=path

    def _getSigningSecret(self):
        if self._shared_secret is not None:
            return self._shared_secret
        manager=getUtility(IKeyManager)
        return manager.secret()

    # ISessionPlugin implementation
    def _setupSession(self, userid, response, tokens=(), user_data=''):
        cookie = tktauth.createTicket(
            secret=self._getSigningSecret(),
            userid=userid,
            tokens=tokens,
            user_data=user_data,
            mod_auth_tkt=self.mod_auth_tkt,
            )
        self._setCookie(cookie, response)

    def _setCookie(self, cookie, response):
        cookie=binascii.b2a_base64(cookie).rstrip()
        # disable secure cookie in development mode, to ease local testing
        if getConfiguration().debug_mode:
            secure = False
        else:
            secure = self.secure
        options = dict(path=self.path, secure=secure, http_only=True)
        if self.cookie_domain:
            options['domain'] = self.cookie_domain
        if self.cookie_lifetime:
            options['expires'] = cookie_expiration_date(self.cookie_lifetime)
        response.setCookie(self.cookie_name, cookie, **options)

    # IExtractionPlugin implementation
    def extractCredentials(self, request):
        creds={}

        if not self.cookie_name in request:
            return creds

        try:
            creds["cookie"]=binascii.a2b_base64(request.get(self.cookie_name))
        except binascii.Error:
            # If we have a cookie which is not properly base64 encoded it
            # can not be ours.
            return creds

        creds["source"]="plone.session" # XXX should this be the id?

        return creds

    # IAuthenticationPlugin implementation
    def authenticateCredentials(self, credentials):
        if not credentials.get("source", None)=="plone.session":
            return None

        ticket=credentials["cookie"]
        ticket_data = self._validateTicket(ticket)
        if ticket_data is None:
            return None
        (digest, userid, tokens, user_data, timestamp) = ticket_data
        pas=self._getPAS()
        info=pas._verifyUser(pas.plugins, user_id=userid)
        if info is None:
            return None

        # XXX Should refresh the ticket if after timeout refresh.
        return (info['id'], info['login'])

    def _validateTicket(self, ticket, now=None):
        if now is None:
            now = time.time()
        if self._shared_secret is not None:
            ticket_data = tktauth.validateTicket(self._shared_secret, ticket,
                timeout=self.timeout, now=now, mod_auth_tkt=self.mod_auth_tkt)
        else:
            ticket_data = None
            manager = queryUtility(IKeyManager)
            if manager is None:
                return None
            for secret in manager[u"_system"]:
                if secret is None:
                    continue
                ticket_data = tktauth.validateTicket(secret, ticket,
                    timeout=self.timeout, now=now, mod_auth_tkt=self.mod_auth_tkt)
                if ticket_data is not None:
                    break
        return ticket_data

    # ICredentialsUpdatePlugin implementation
    def updateCredentials(self, request, response, login, new_password):
        pas=self._getPAS()
        info=pas._verifyUser(pas.plugins, login=login)
        if info is not None:
            # Only setup a session for users in our own user folder.
            self._setupSession(info["id"], response)

    # ICredentialsResetPlugin implementation
    def resetCredentials(self, request, response):
        response=self.REQUEST["RESPONSE"]
        if self.cookie_domain:
            response.expireCookie(
                self.cookie_name, path=self.path, domain=self.cookie_domain)
        else:
            response.expireCookie(self.cookie_name, path=self.path)

    manage_secret = PageTemplateFile("secret.pt", globals())

    security.declareProtected(ManageUsers, 'manage_clearSecrets')
    @postonly
    def manage_clearSecrets(self, REQUEST):
        """Clear all secrets from this source. This invalidates all current
        sessions and requires users to login again.
        """
        manager=getUtility(IKeyManager)
        manager.clear()
        manager.rotate()
        response = REQUEST.response
        response.redirect('%s/manage_secret?manage_tabs_message=%s' %
            (self.absolute_url(), 'All+secrets+cleared.'))

    security.declareProtected(ManageUsers, 'manage_createNewSecret')
    @postonly
    def manage_createNewSecret(self, REQUEST):
        """Create a new (signing) secret.
        """
        manager=getUtility(IKeyManager)
        manager.rotate()
        response = REQUEST.response
        response.redirect('%s/manage_secret?manage_tabs_message=%s' %
            (self.absolute_url(), 'New+secret+created.'))

    security.declareProtected(ManageUsers, 'haveSharedSecret')
    def haveSharedSecret(self):
        return self._shared_secret is not None

    security.declareProtected(ManageUsers, 'manage_removeSharedSecret')
    @postonly
    def manage_removeSharedSecret(self, REQUEST):
        """Clear the shared secret. This invalidates all current sessions and
        requires users to login again.
        """
        self._shared_secret = None
        response = REQUEST.response
        response.redirect('%s/manage_secret?manage_tabs_message=%s' %
            (self.absolute_url(), 'Shared+secret+removed.'))

    security.declareProtected(ManageUsers, 'manage_setSharedSecret')
    @postonly
    def manage_setSharedSecret(self, REQUEST):
        """Set the shared secret.
        """
        secret = REQUEST.get('shared_secret')
        response = REQUEST.response
        if not secret:
            response.redirect('%s/manage_secret?manage_tabs_message=%s' %
                (self.absolute_url(), 'Shared+secret+must+not+be+blank.'))
            return
        self._shared_secret = secret
        response.redirect('%s/manage_secret?manage_tabs_message=%s' %
            (self.absolute_url(), 'New+shared+secret+set.'))

    def _refreshSession(self, request, now=None):
        # Refresh a ticket. Does *not* check the user is in the use folder
        if not self.cookie_name in request:
            return None
        try:
            ticket = binascii.a2b_base64(request.get(self.cookie_name))
        except binascii.Error:
            return None
        if now is None:
            now = time.time()
        ticket_data = self._validateTicket(ticket, now)
        if ticket_data is None:
            return None
        (digest, userid, tokens, user_data, timestamp) = ticket_data
        self._setupSession(userid, request.response, tokens, user_data)
        return True

    def _refresh_content(self, REQUEST):
        setHeader = REQUEST.response.setHeader
        type = REQUEST.get('type')
        if type == 'gif':
            setHeader('Content-Type', 'image/gif')
            return EMPTY_GIF
        elif type == 'css':
            setHeader('Content-Type', 'text/css')
            return ""
        elif type == 'js':
            setHeader('Content-Type', 'text/javascript')
            return ""
        #if content:
        #    return "still_logged_in = still_logged_in;\n"
        #else:
        #    return "still_logged_in = false;\n"

    security.declarePublic('refresh')
    def refresh(self, REQUEST):
        """Refresh the cookie"""
        setHeader = REQUEST.response.setHeader
        # Disable HTTP 1.0 Caching
        setHeader('Expires', formatdate(0, usegmt=True))
        if self.refresh_interval < 0:
            return self._refresh_content(REQUEST)
        now = time.time()
        refreshed = self._refreshSession(REQUEST, now)
        if not refreshed:
            # We have an unauthenticated user
            setHeader('Cache-Control', 'public, must-revalidate, max-age=%d, s-max-age=86400' % self.refresh_interval)
            setHeader('Vary', 'Cookie')
        else:
            setHeader('Cache-Control', 'private, must-revalidate, proxy-revalidate, max-age=%d, s-max-age=0' % self.refresh_interval)
        return self._refresh_content(REQUEST)

    security.declarePublic('remove')
    def remove(self, REQUEST):
        """Remove the cookie"""
        self.resetCredentials(REQUEST, REQUEST.response)
        setHeader = REQUEST.response.setHeader
        # Disable HTTP 1.0 Caching
        setHeader('Expires', formatdate(0, usegmt=True))
        setHeader('Cache-Control', 'public, must-revalidate, max-age=0, s-max-age=86400')
        return self._refresh_content(REQUEST)


classImplements(SessionPlugin, ISessionPlugin,
                IExtractionPlugin, IAuthenticationPlugin,
                ICredentialsResetPlugin, ICredentialsUpdatePlugin)

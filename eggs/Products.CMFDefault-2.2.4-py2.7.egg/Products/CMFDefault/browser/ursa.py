from Products.CMFDefault.utils import Message as _
from Products.CMFDefault.utils import decode
from Products.CMFDefault.browser.utils import ViewBase
from Products.CMFDefault.browser.utils import memoize

class UrsineGlobals(ViewBase):
    """ Provide lazy / efficient template-level globals.

    o Replaces 'getMainGlobals' in stock skin.
    """
    def __init__(self, context, request):
        super(ViewBase, self).__init__(context, request)
        ct = self.request.RESPONSE.getHeader('content-type') or ''
        if not 'charset' in ct:
            # Some newstyle views set a different charset - don't override it.
            # Oldstyle views need the default_charset.
            default_charset = self.ptool.getProperty('default_charset', None)
            if default_charset:
                self.request.RESPONSE.setHeader('content-type',
                              'text/html; charset=%s' % default_charset)

    @property
    @memoize
    def ptool(self):
        return self._getTool('portal_properties')

    @property
    @memoize
    def utool(self):
        return self._getTool('portal_url')

    @property
    @memoize
    def mtool(self):
        return self._getTool('portal_membership')

    @property
    @memoize
    def atool(self):
        return self._getTool('portal_actions')

    @property
    @memoize
    def wtool(self):
        return self._getTool('portal_workflow')

    @property
    @memoize
    def portal_object(self):
        return self.utool.getPortalObject()

    @property
    @memoize
    def portal_url(self):
        return self.utool()

    @property
    @memoize
    def portal_title(self):
        return self.portal_object.Title()

    @property
    @memoize
    def object_title(self):
        return self.context.Title()

    @property
    @memoize
    def object_description(self):
        return self.context.Description()

    @property
    @memoize
    def trunc_id(self):
        id = self.context.getId()
        if len(id) > 15:
            id = id[:15] + '...'
        return id

    @property
    @memoize
    def icon(self):
        return getattr(self.context, 'getIconURL',
                        lambda: getattr(self.context, 'icon', ''))()
    @property
    @memoize
    def typename(self):
        return self.context.getPortalTypeName()

    @property
    @memoize
    def wf_state(self):
        return self.wtool.getInfoFor(self.context, 'review_state', '')

    @property
    @memoize
    def page_title(self):
        site_title = self.portal_title
        page_title = self.object_title

        if page_title != site_title:
            page_title = site_title + ": " + page_title

        return decode(page_title, self.context)

    @property
    @memoize
    def breadcrumbs(self):
        # XXX Shouldn't we just be walking up the aq_inner chain?
        result = [{'id': _(u'root'),
                   'title' : self.ptool.title(),
                   'url' : self.portal_url,
                  }]

        relative = self.utool.getRelativeContentPath(self.context)
        portal = self.portal_object

        for i, token in enumerate(relative):
            now = relative[:i+1]
            obj = portal.unrestrictedTraverse(now)
            if token != 'talkback':
                result.append({'id': token,
                               'title': obj.Title(),
                               'url': obj.absolute_url(),
                              })

        return result

    @property
    @memoize
    def member(self):
        return self.mtool.getAuthenticatedMember()

    @property
    @memoize
    def membername(self):
        return self.isAnon and 'Guest' or self.member.getUserName()

    @property
    @memoize
    def membersfolder(self):
        return self.mtool.getMembersFolder()

    @property
    @memoize
    def isAnon(self):
        return self.mtool.isAnonymousUser()

    @property
    @memoize
    def uname(self):
        return self.isAnon and 'Guest' or self.member.getUserName()

    @property
    @memoize
    def status_message(self):
        message = self.request.form.get('portal_status_message')
        if message is not None:
            message = decode(message, self.context)
        return message
 
    @property
    @memoize
    def actions(self):
        return self.atool.listFilteredActionsFor(self.context)
    
    @property
    @memoize
    def user_actions(self):
        return self.actions['user']
    
    @property
    @memoize
    def object_actions(self):
        return self.actions['object']
    
    @property
    @memoize
    def workflow_actions(self):
        return self.actions['workflow']
    
    @property
    @memoize
    def folder_actions(self):
        return self.actions['folder']
    
    @property
    @memoize
    def global_actions(self):
        return self.actions['global']
    
    @property
    @memoize
    def add_actions(self):
        return self.actions.get('folder/add', ())

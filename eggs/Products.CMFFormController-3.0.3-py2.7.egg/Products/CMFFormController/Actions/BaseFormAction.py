from zope.tales.tales import CompilerError
from zope.interface import implements

from AccessControl import ClassSecurityInfo
from Acquisition import aq_base, aq_parent, aq_inner
from Products.CMFCore.Expression import Expression
from Products.PageTemplates.Expressions import getEngine
from Products.PageTemplates.Expressions import SecureModuleImporter

from Products.CMFCore.utils import getToolByName
from Products.CMFFormController.config import URL_ENCODING
from Products.CMFFormController.utils import log
from IFormAction import IFormAction
from ZTUtils.Zope import make_query

try:
    from OFS.role import RoleManager
except ImportError:
    # Zope <=2.12
    from AccessControl.Role import RoleManager


class BaseFormAction(RoleManager):
    implements(IFormAction,)

    security = ClassSecurityInfo()
    security.declareObjectPublic()
    security.setDefaultAccess('allow')

    expression = None

    def __init__(self, arg=None):
        if arg is None:
            log('No argument specified for action.  This means that some of your CMFFormController actions may have been corrupted.  You may be able to fix them by editing the actions in question via the Actions tab and re-saving them.')
        else:
            try:
                self.expression = Expression(arg)
            except:
                raise CompilerError, 'Bad action expression %s' % str(arg)


    def __call__(self, controller_state):
        raise NotImplementedError


    def getArg(self, controller_state):
        """Generate an expression context for the TALES expression used as
        the argument to the action and evaluate the expression."""
        context = controller_state.getContext()

        portal = getToolByName(context, 'portal_url').getPortalObject()
        portal_membership = getToolByName(portal, 'portal_membership')

        if context is None or not hasattr(context, 'aq_base'):
            folder = portal
        else:
            folder = context
            # Search up the containment hierarchy until we find an
            # object that claims to be a folder.
            while folder is not None:
                if getattr(aq_base(folder), 'isPrincipiaFolderish', 0):
                    # found it.
                    break
                else:
                    folder = aq_parent(aq_inner(folder))

        object_url = context.absolute_url()

        if portal_membership.isAnonymousUser():
            member = None
        else:
            member = portal_membership.getAuthenticatedMember()
        data = {
            'object_url':   object_url,
            'folder_url':   folder.absolute_url(),
            'portal_url':   portal.absolute_url(),
            'object':       context,
            'folder':       folder,
            'portal':       portal,
            'nothing':      None,
            'request':      getattr( context, 'REQUEST', None ),
            'modules':      SecureModuleImporter,
            'member':       member,
            'state':        controller_state,
            }
        exprContext = getEngine().getContext(data)
        return self.expression(exprContext)


    def combineArgs(self, url, kwargs):
        """Utility method that takes a URL, parses its existing query string,
        and combines the resulting dict with kwargs"""
        import urlparse
        import cgi

        # parse the existing URL
        parsed_url = list(urlparse.urlparse(url))
        # get the existing query string
        qs = parsed_url[4]
        # parse the query into a dict
        d = cgi.parse_qs(qs, 1)
        # update with stuff from kwargs
        for k, v in kwargs.items():
            if isinstance(v, unicode):
                v = v.encode(URL_ENCODING)
            d[k] = [v] # put in a list to be consistent with parse_qs
        # parse_qs behaves a little unexpectedly -- all query string args
        # are represented as lists.  I think the reason is so that you get
        # consistent behavior for things like http://myurl?a=1&a=2&a=3
        # For this case parse_qs returns d['a'] = ['1','2','3']
        # However, that means that http://myurl?a=1 comes back as d['a']=['1']
        # unmunge some of parse_qs's weirdness
        dnew = {}
        for k, v in d.items():
            if v and len(v) == 1:
                dnew[k] = v[0]
            else:
                dnew[k] = v
        return dnew


    def updateQuery(self, url, kwargs):
        """Utility method that takes a URL, parses its existing query string,
        url encodes
        and updates the query string using the values in kwargs"""
        d = self.combineArgs(url, kwargs)

        import urlparse

        # parse the existing URL
        parsed_url = list(urlparse.urlparse(url))

        # re-encode the string
        # We use ZTUtils.make_query here because it
        # does Zope-specific marshalling of lists,
        # dicts, integers and DateTime.
        # XXX *Normal* people should not be affected by this.
        # but one can argue about the need of using
        # standard query encoding instead for non-Zope
        # destination urls.
        parsed_url[4] = make_query(**d)
        # rebuild the URL
        return urlparse.urlunparse(parsed_url)


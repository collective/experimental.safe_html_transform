import urlparse
from urllib import quote

from zope.interface import implements

from Products.CMFCore.permissions import View
from Products.CMFCore.permissions import ModifyPortalContent
from AccessControl import ClassSecurityInfo

from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import StringField
from Products.Archetypes.atapi import StringWidget

from Products.ATContentTypes.config import PROJECTNAME
from Products.ATContentTypes.content.base import registerATCT
from Products.ATContentTypes.content.base import ATCTContent
from Products.ATContentTypes.content.schemata import ATContentTypeSchema
from Products.ATContentTypes.content.schemata import finalizeATCTSchema
from Products.ATContentTypes.interfaces import IATLink

from Products.ATContentTypes import ATCTMessageFactory as _

ATLinkSchema = ATContentTypeSchema.copy() + Schema((
    StringField('remoteUrl',
        required=True,
        searchable=True,
        primary=True,
        default="http://",
        # either mailto, absolute url or relative url
        validators=(),
        widget=StringWidget(
            description='',
            label=_(u'label_url', default=u'URL'),
            maxlength='511',
            )),
    ))
finalizeATCTSchema(ATLinkSchema)


class ATLink(ATCTContent):
    """A link to an internal or external resource."""

    schema = ATLinkSchema

    portal_type = 'Link'
    archetype_name = 'Link'
    _atct_newTypeFor = {'portal_type': 'CMF Link', 'meta_type': 'Link'}
    assocMimetypes = ()
    assocFileExt = ('link', 'url', )
    cmf_edit_kws = ('remote_url', )

    implements(IATLink)

    security = ClassSecurityInfo()

    security.declareProtected(ModifyPortalContent, 'setRemoteUrl')
    def setRemoteUrl(self, value, **kwargs):
        """remute url mutator

        Use urlparse to sanify the url
        Also see http://dev.plone.org/plone/ticket/3296
        """
        if value:
            value = urlparse.urlunparse(urlparse.urlparse(value))
        self.getField('remoteUrl').set(self, value, **kwargs)

    security.declareProtected(View, 'remote_url')
    def remote_url(self):
        """CMF compatibility method
        """
        return self.getRemoteUrl()

    security.declarePrivate('cmf_edit')
    def cmf_edit(self, remote_url=None, **kwargs):
        if not remote_url:
            remote_url = kwargs.get('remote_url', None)
        self.update(remoteUrl=remote_url, **kwargs)

    security.declareProtected(View, 'getRemoteUrl')
    def getRemoteUrl(self):
        """Sanitize output
        """
        value = self.Schema()['remoteUrl'].get(self)
        if not value: value = ''  # ensure we have a string
        return quote(value, safe='?$#@/:=+;$,&%')

registerATCT(ATLink, PROJECTNAME)

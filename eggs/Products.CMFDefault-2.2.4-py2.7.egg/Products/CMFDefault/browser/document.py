##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Browser views for documents. """

from zope.component import adapts
from zope.formlib import form
from zope.interface import implements
from zope.interface import Interface
from zope.schema import ASCIILine
from zope.schema import Bytes
from zope.schema import Choice
from zope.schema import Text
from zope.schema import TextLine

from Products.CMFDefault.Document import REST_AVAILABLE
from Products.CMFDefault.formlib.form import ContentEditFormBase
from Products.CMFDefault.formlib.schema import ProxyFieldProperty
from Products.CMFDefault.formlib.schema import SchemaAdapterBase
from Products.CMFDefault.formlib.vocabulary import StaticVocabulary
from Products.CMFDefault.formlib.widgets import ChoiceRadioWidget
from Products.CMFDefault.formlib.widgets import TextInputWidget
from Products.CMFDefault.interfaces import IMutableDocument
from Products.CMFDefault.utils import Message as _

from utils import decode
from utils import memoize
from utils import ViewBase

available_text_formats = (
        (u'structured-text', 'structured-text', _(u'structured-text')),
        (u'plain', 'plain', _(u'plain text')),
        (u'html', 'html', _(u'html')))

if REST_AVAILABLE:
    available_text_formats +=  ( ( u'restructured-text'
                                 , 'restructured-text'
                                 , _(u'restructured-text')
                                 ), )

TextFormatVocabularyFactory = StaticVocabulary(available_text_formats)


class IDocumentSchema(Interface):

    """Schema for document views.
    """

    safety_belt = ASCIILine(
        required=False)

    title = TextLine(
        title=_(u'Title'),
        readonly=True)

    description = Text(
        title=_(u'Description'),
        readonly=True)

    text_format = Choice(
        title=_(u'Format'),
        vocabulary='cmf.AvailableTextFormats')

    upload = Bytes(
        title=_(u'Upload'),
        required=False)

    text = Text(
        title=_(u'Body'),
        required=False,
        missing_value=u'')


class DocumentSchemaAdapter(SchemaAdapterBase):

    """Adapter for IMutableDocument.
    """

    adapts(IMutableDocument)
    implements(IDocumentSchema)

    safety_belt = ProxyFieldProperty(IDocumentSchema['safety_belt'],
                                     '_safety_belt')
    title = ProxyFieldProperty(IDocumentSchema['title'], 'Title')
    description = ProxyFieldProperty(IDocumentSchema['description'],
                                     'Description')
    text_format = ProxyFieldProperty(IDocumentSchema['text_format'])
    upload = None
    text = ProxyFieldProperty(IDocumentSchema['text'],
                              'EditableBody', '_edit')


class DocumentView(ViewBase):

    """View for IDocument.
    """

    # interface

    @memoize
    @decode
    def text(self):
        return self.context.CookedBody()


class DocumentEditView(ContentEditFormBase):

    """Edit view for IMutableDocument.
    """

    form_fields = form.FormFields(IDocumentSchema)
    form_fields['text_format'].custom_widget = ChoiceRadioWidget
    form_fields['text'].custom_widget = TextInputWidget

    def setUpWidgets(self, ignore_request=False):
        super(DocumentEditView,
              self).setUpWidgets(ignore_request=ignore_request)
        self.widgets['safety_belt'].hide = True
        self.widgets['description'].height = 3
        self.widgets['text_format'].orientation = 'horizontal'
        self.widgets['upload'].displayWidth = 60
        self.widgets['text'].height = 20

    def _handle_success(self, action, data):
        body = data.get('upload')
        if body:
            data['text'] = body.decode(self._getDefaultCharset())
        changed = super(DocumentEditView, self)._handle_success(action, data)
        if changed:
            self.context.updateSafetyBelt(data.get('safety_belt'))
        return changed

    def handle_validate(self, action, data):
        errors = super(DocumentEditView, self).handle_validate(action, data)
        if errors:
            return errors
        safety_belt = self.request.form['form.safety_belt']
        if not self.context.isValidSafetyBelt(safety_belt):
            return (_(u'Intervening changes from elsewhere detected. Please '
                      u'refetch the document and reapply your changes.'),)
        # make sure applyChanges doesn't try to update safety_belt
        self.request.form['form.safety_belt'] = self.context._safety_belt
        return None

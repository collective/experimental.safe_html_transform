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
"""Formlib form base classes. """

from datetime import datetime
from sets import Set

from AccessControl.SecurityInfo import ClassSecurityInfo
from App.class_init import InitializeClass
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from five.formlib.formbase import PageAddForm
from five.formlib.formbase import PageDisplayForm
from five.formlib.formbase import PageForm
from zope.component import adapts
from zope.component import getUtility
from zope.component.interfaces import IFactory
from zope.container.interfaces import INameChooser
from zope.datetime import parseDatetimetz
from zope.formlib import form
from zope.formlib.interfaces import IPageForm
from zope.interface import implementsOnly
from zope.schema import ASCIILine
from ZTUtils import make_query

from Products.CMFCore.interfaces import IFolderish
from Products.CMFCore.interfaces import ITypeInformation
from Products.CMFDefault.browser.utils import ViewBase
from Products.CMFDefault.exceptions import AccessControl_Unauthorized
from Products.CMFDefault.formlib.widgets import IDInputWidget
from Products.CMFDefault.interfaces import ICMFDefaultSkin
from Products.CMFDefault.permissions import AddPortalContent
from Products.CMFDefault.utils import Message as _
from Products.CMFDefault.utils import translate


class _EditFormMixin(ViewBase):

    template = ViewPageTemplateFile('editform.pt')

    def _setRedirect(self, provider_id, action_path, keys=''):
        provider = self._getTool(provider_id)
        try:
            target = provider.getActionInfo(action_path, self.context)['url']
        except ValueError:
            target = self._getPortalURL()

        kw = {}
        if self.status:
            message = translate(self.status, self.context)
            if isinstance(message, unicode):
                message = message.encode(self._getBrowserCharset())
            kw['portal_status_message'] = message
        for k in keys.split(','):
            k = k.strip()
            v = self.request.form.get(k, None)
            if v:
                kw[k] = v

        query = kw and ( '?%s' % make_query(kw) ) or ''
        self.request.RESPONSE.redirect( '%s%s' % (target, query) )

        return ''

    def handle_failure(self, action, data, errors):
        if self.status:
            message = translate(self.status, self.context)
            self.request.other['portal_status_message'] = message


class EditFormBase(_EditFormMixin, PageForm):

    pass


class ContentAddFormBase(_EditFormMixin, PageAddForm):

    adapts(IFolderish, ICMFDefaultSkin, ITypeInformation)
    implementsOnly(IPageForm)

    security = ClassSecurityInfo()
    security.declareObjectPrivate()

    actions = form.Actions(
        form.Action(
            name='add',
            label=form._('Add'),
            condition=form.haveInputWidgets,
            success='handle_add',
            failure='handle_failure'),
        form.Action(
            name='cancel',
            label=_(u'Cancel'),
            success='handle_cancel_success',
            failure='handle_cancel_failure'))

    def __init__(self, context, request, ti):
        self.context = context
        self.request = request
        self.ti = ti

    security.declareProtected(AddPortalContent, '__call__')
    def __call__(self):
        container = self.context
        portal_type = self.ti.getId()

        # check allowed (sometimes redundant, but better safe than sorry)
        if not self.ti.isConstructionAllowed(container):
            raise AccessControl_Unauthorized('Cannot create %s' % portal_type)

        # check container constraints
        ttool = self._getTool('portal_types')
        container_ti = ttool.getTypeInfo(container)
        if container_ti is not None and \
                not container_ti.allowType(portal_type):
            raise ValueError('Disallowed subobject type: %s' % portal_type)

        return super(ContentAddFormBase, self).__call__()

    @property
    def label(self):
        obj_type = translate(self.ti.Title(), self.context)
        return _(u'Add ${obj_type}', mapping={'obj_type': obj_type})

    @property
    def description(self):
        return self.ti.Description()

    #same as in form.AddFormBase but without action decorator
    def handle_add(self, action, data):
        self.createAndAdd(data)

    def handle_cancel_success(self, action, data):
        return self._setRedirect('portal_types',
                                 ('object/folderContents', 'object/view'))

    def handle_cancel_failure(self, action, data, errors):
        self.status = None
        return self._setRedirect('portal_types',
                                 ('object/folderContents', 'object/view'))

    def create(self, data):
        id =  data.pop('id', '') or ''
        factory = getUtility(IFactory, self.ti.factory)
        obj = factory(id=id, **data)
        obj._setPortalTypeName(self.ti.getId())
        return obj

    def add(self, obj):
        container = self.context

        name = INameChooser(container).chooseName(obj.getId(), obj)
        obj.id = name
        container._setObject(name, obj)
        obj = container._getOb(name)

        obj_type = translate(obj.Type(), container)
        self.status = _(u'${obj_type} added.', mapping={'obj_type': obj_type})
        self._finished_add = True
        self._added_obj = obj
        return obj

    def nextURL(self):
        obj = self._added_obj

        message = translate(self.status, self.context)
        if isinstance(message, unicode):
            message = message.encode(self._getBrowserCharset())
        return '%s/%s?%s' % (obj.absolute_url(), self.ti.immediate_view,
                             make_query(portal_status_message=message))

InitializeClass(ContentAddFormBase)


class FallbackAddView(ContentAddFormBase):

    """Add view for IDynamicType content.
    """

    form_fields = form.FormFields(ASCIILine(__name__='id', title=_(u'ID')))
    form_fields['id'].custom_widget = IDInputWidget

    def createAndAdd(self, data):
        if not self.ti.product:
            return super(FallbackAddView, self).createAndAdd(data)

        # for portal types with oldstyle factories
        container = self.context
        name = container.invokeFactory(self.ti.getId(), data['id'])
        obj = container._getOb(name)

        obj_type = translate(obj.Type(), container)
        self.status = _(u'${obj_type} added.', mapping={'obj_type': obj_type})
        self._finished_add = True
        self._added_obj = obj
        return obj


class ContentEditFormBase(_EditFormMixin, PageForm):

    actions = form.Actions(
        form.Action(
            name='change',
            label=_(u'Change'),
            validator='handle_validate',
            success='handle_change_success',
            failure='handle_failure'),
        form.Action(
            name='change_and_view',
            label=_(u'Change and View'),
            validator='handle_validate',
            success='handle_change_and_view_success',
            failure='handle_failure'))

    description = u''

    def setUpWidgets(self, ignore_request=False):
        self.adapters = {}
        self.widgets = form.setUpEditWidgets(
            self.form_fields, self.prefix, self.context, self.request,
            adapters=self.adapters, ignore_request=ignore_request
            )

    @property
    def label(self):
        obj_type = translate(self.context.Type(), self.context)
        return _(u'Edit ${obj_type}', mapping={'obj_type': obj_type})

    @property
    def successMessage(self):
        obj_type = translate(self.context.Type(), self.context)
        return _(u'${obj_type} changed.', mapping={'obj_type': obj_type})

    noChangesMessage = _(u'Nothing to change.')

    def handle_validate(self, action, data):
        if self.context.wl_isLocked():
            return (_(u'This resource is locked via webDAV.'),)
        return None

    def applyChanges(self, data):
        content = self.context
        changes = form.applyData(content, self.form_fields, data,
                                 self.adapters)
        # ``changes`` is a dictionary; if empty, there were no changes
        if changes:
            content.reindexObject()
        return changes

    def _handle_success(self, action, data):
        # normalize set and datetime
        for k, v in data.iteritems():
            if isinstance(v, Set):
                data[k] = set(v)
            elif isinstance(v, datetime) and v.tzname() is None:
                data[k] = parseDatetimetz(str(v))
        changes = self.applyChanges(data)
        if changes:
            self.status = self.successMessage
        else:
            self.status = self.noChangesMessage
        return changes

    def handle_change_success(self, action, data):
        self._handle_success(action, data)
        return self._setRedirect('portal_types', 'object/edit')

    def handle_change_and_view_success(self, action, data):
        self._handle_success(action, data)
        return self._setRedirect('portal_types', 'object/view')


class DisplayFormBase(PageDisplayForm, ViewBase):

    template = ViewPageTemplateFile('viewform.pt')

    @property
    def label(self):
        return self.context.Type()

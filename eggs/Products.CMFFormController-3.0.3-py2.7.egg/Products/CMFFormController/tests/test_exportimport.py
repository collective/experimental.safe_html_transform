##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""CMFFormController setup handler unit tests.
"""
import unittest

from Products.GenericSetup.tests.common import BaseRegistryTests
from Products.GenericSetup.tests.common import DummyExportContext
from Products.GenericSetup.tests.common import DummyImportContext
from Products.CMFFormController.FormAction import FormAction
from Products.CMFFormController.FormValidator import FormValidator

class _CMFFormControllerSetup(BaseRegistryTests):

    V_OBJECT_ID = 'v_object_id'
    V_CONTEXT_TYPE = 'v_context_type'
    V_BUTTON = 'v_button'
    V_VALIDATORS = ['validator1', 'validator2']

    A_OBJECT_ID = 'a_object_id'
    A_STATUS = 'a_status'
    A_CONTEXT_TYPE = 'a_context_type'
    A_BUTTON = 'a_button'
    A_ACTION_TYPE = 'redirect_to'
    A_ACTION_ARG = 'string:action_arg'

    _EMPTY_EXPORT = """\
<?xml version="1.0"?>
<cmfformcontroller>
</cmfformcontroller>
"""

    _WITH_INFO_EXPORT = """\
<?xml version="1.0"?>
<cmfformcontroller>
   <action
     object_id="%s"
     status="%s"
     context_type="%s"
     button="%s"
     action_type="%s"
     action_arg="%s"
     />
   <validator
     object_id="%s"
     context_type="%s"
     button="%s"
     validators="%s"
     />
</cmfformcontroller>
""" % (A_OBJECT_ID,
       A_STATUS,
       A_CONTEXT_TYPE,
       A_BUTTON,
       A_ACTION_TYPE,
       A_ACTION_ARG,
       V_OBJECT_ID,
       V_CONTEXT_TYPE,
       V_BUTTON,
       ','.join(V_VALIDATORS),
      )

    _WITH_PARTIAL_INFO_EXPORT = """\
<?xml version="1.0"?>
<cmfformcontroller>
   <action
     object_id="%s"
     status="%s"
     action_type="%s"
     action_arg="%s"
     />
   <validator
     object_id="%s"
     validators="%s"
     />
</cmfformcontroller>
""" % (A_OBJECT_ID,
       A_STATUS,
       A_ACTION_TYPE,
       A_ACTION_ARG,
       V_OBJECT_ID,
       ','.join(V_VALIDATORS),
      )

    def _initSite(self, with_info=False):
        from OFS.Folder import Folder
        from Products.CMFFormController.FormController import FormController

        self.root.site = Folder(id='site')
        site = self.root.site
        mgr = FormController()
        site._setObject( mgr.getId(), mgr )

        if with_info:
            fc = getattr(site, mgr.getId())

            fc.actions.set(FormAction(self.A_OBJECT_ID, self.A_STATUS, self.A_CONTEXT_TYPE, self.A_BUTTON, self.A_ACTION_TYPE, self.A_ACTION_ARG))
            fc.validators.set(FormValidator(self.V_OBJECT_ID, self.V_CONTEXT_TYPE, self.V_BUTTON, ','.join(self.V_VALIDATORS)))

        return site


class CMFFormControllerExportConfiguratorTests(_CMFFormControllerSetup):

    def _getTargetClass(self):
        from Products.CMFFormController.exportimport \
                import CMFFormControllerExportConfigurator

        return CMFFormControllerExportConfigurator

    def test_generateXML_empty(self):
        site = self._initSite(with_info=False)
        configurator = self._makeOne(site).__of__(site)

        self._compareDOM(configurator.generateXML(), self._EMPTY_EXPORT)

    def test_generateXML_with_info(self):
        site = self._initSite(with_info=True)
        configurator = self._makeOne(site).__of__(site)

        self._compareDOM(configurator.generateXML(), self._WITH_INFO_EXPORT)


class CMFFormControllerImportConfiguratorTests(_CMFFormControllerSetup):

    def _getTargetClass(self):
        from Products.CMFFormController.exportimport \
                import CMFFormControllerImportConfigurator

        return CMFFormControllerImportConfigurator

    def test_parseXML_empty(self):
        site = self._initSite(with_info=False)
        configurator = self._makeOne(site)
        fc_info = configurator.parseXML(self._EMPTY_EXPORT)

        self.assertEqual(len(fc_info['actions']), 0)
        self.assertEqual(len(fc_info['validators']), 0)

    def test_parseXML_with_info(self):
        site = self._initSite(with_info=False)
        configurator = self._makeOne(site)
        fc_info = configurator.parseXML(self._WITH_INFO_EXPORT)

        self.assertEqual(len(fc_info['actions']), 1)
        self.assertEqual(len(fc_info['validators']), 1)

        info = fc_info['actions'][0]
        self.assertEqual(info['object_id'], self.A_OBJECT_ID)
        self.assertEqual(info['status'], self.A_STATUS)
        self.assertEqual(info['context_type'], self.A_CONTEXT_TYPE)
        self.assertEqual(info['button'], self.A_BUTTON)
        self.assertEqual(info['action_type'], self.A_ACTION_TYPE)
        self.assertEqual(info['action_arg'], self.A_ACTION_ARG)
        info = fc_info['validators'][0]
        self.assertEqual(info['object_id'], self.V_OBJECT_ID)
        self.assertEqual(info['context_type'], self.V_CONTEXT_TYPE)
        self.assertEqual(info['button'], self.V_BUTTON)
        self.assertEqual(info['validators'], ','.join(self.V_VALIDATORS))


class Test_exportCMFFormController(_CMFFormControllerSetup):

    def test_empty(self):
        from Products.CMFFormController.exportimport \
             import exportCMFFormController

        site = self._initSite(with_info=False)
        context = DummyExportContext(site)
        exportCMFFormController(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'cmfformcontroller.xml')
        self._compareDOM(text, self._EMPTY_EXPORT)
        self.assertEqual(content_type, 'text/xml')

    def test_with_info(self):
        from Products.CMFFormController.exportimport \
             import exportCMFFormController

        site = self._initSite(with_info=True)
        context = DummyExportContext(site)
        exportCMFFormController(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'cmfformcontroller.xml')
        self._compareDOM(text, self._WITH_INFO_EXPORT)
        self.assertEqual(content_type, 'text/xml')


class Test_importCMFFormController(_CMFFormControllerSetup):

    def test_normal(self):
        from Products.CMFFormController.exportimport \
             import importCMFFormController

        site = self._initSite(with_info=False)
        fc = site.portal_form_controller

        self.assertEqual(len(fc.listFormValidators()), 0)
        self.assertEqual(len(fc.listFormActions()), 0)

        context = DummyImportContext(site)
        context._files['cmfformcontroller.xml'] = self._WITH_INFO_EXPORT
        importCMFFormController(context)

        self.assertEqual(len(fc.listFormActions()), 1)
        self.assertEqual(len(fc.listFormValidators()), 1)

        action = fc.listFormActions()[0]
        self.assertEqual(action.getObjectId(), self.A_OBJECT_ID)
        self.assertEqual(action.getStatus(), self.A_STATUS)
        self.assertEqual(action.getContextType(), self.A_CONTEXT_TYPE)
        self.assertEqual(action.getButton(), self.A_BUTTON)
        self.assertEqual(action.getActionType(), self.A_ACTION_TYPE)
        self.assertEqual(action.getActionArg(), self.A_ACTION_ARG)

        validator = fc.listFormValidators()[0]
        self.assertEqual(validator.getObjectId(), self.V_OBJECT_ID)
        self.assertEqual(validator.getContextType(), self.V_CONTEXT_TYPE)
        self.assertEqual(validator.getButton(), self.V_BUTTON)
        self.assertEqual(validator.getValidators(), self.V_VALIDATORS)

    def test_partial(self):
        from Products.CMFFormController.exportimport \
             import importCMFFormController

        site = self._initSite(with_info=False)
        fc = site.portal_form_controller

        self.assertEqual(len(fc.listFormValidators()), 0)
        self.assertEqual(len(fc.listFormActions()), 0)

        context = DummyImportContext(site)
        context._files['cmfformcontroller.xml'] = self._WITH_PARTIAL_INFO_EXPORT
        importCMFFormController(context)

        self.assertEqual(len(fc.listFormActions()), 1)
        self.assertEqual(len(fc.listFormValidators()), 1)

        action = fc.listFormActions()[0]
        self.assertEqual(action.getObjectId(), self.A_OBJECT_ID)
        self.assertEqual(action.getStatus(), self.A_STATUS)
        self.assertEqual(action.getContextType(), None)
        self.assertEqual(action.getButton(), None)
        self.assertEqual(action.getActionType(), self.A_ACTION_TYPE)
        self.assertEqual(action.getActionArg(), self.A_ACTION_ARG)

        validator = fc.listFormValidators()[0]
        self.assertEqual(validator.getObjectId(), self.V_OBJECT_ID)
        self.assertEqual(validator.getContextType(), None)
        self.assertEqual(validator.getButton(), None)
        self.assertEqual(validator.getValidators(), self.V_VALIDATORS)

    def test_action_not_unicode(self):
        # The action arg cannot be unicode for unrestrictedTraverse
        # calls to work properly
        from Products.CMFFormController.exportimport \
             import importCMFFormController

        site = self._initSite(with_info=False)
        fc = site.portal_form_controller

        context = DummyImportContext(site)
        context._files['cmfformcontroller.xml'] = self._WITH_INFO_EXPORT
        importCMFFormController(context)

        action = fc.listFormActions()[0]
        self.failUnless(isinstance(action.getActionArg(), str))


def test_suite():
    return unittest.TestSuite((
        # TODO disabled broken tests
        # unittest.makeSuite(CMFFormControllerExportConfiguratorTests),
        # unittest.makeSuite(Test_exportCMFFormController),
        unittest.makeSuite(CMFFormControllerImportConfiguratorTests),
        unittest.makeSuite(Test_importCMFFormController),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

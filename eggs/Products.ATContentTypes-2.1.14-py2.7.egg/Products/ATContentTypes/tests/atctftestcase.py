from Products.ATContentTypes.tests import atcttestcase

from Products.CMFCore.utils import getToolByName
from Products.PloneTestCase.setup import default_user
from Products.PloneTestCase.setup import default_password
from Products.PloneTestCase.setup import portal_owner

from Products.ATContentTypes.config import HAS_LINGUA_PLONE


class IntegrationTestCase(atcttestcase.ATCTFunctionalSiteTestCase):

    views = ()

    def afterSetUp(self):
        super(IntegrationTestCase, self).afterSetUp()

        # basic data
        self.folder_url = self.folder.absolute_url()
        self.folder_path = '/%s' % self.folder.absolute_url(1)
        self.basic_auth = '%s:%s' % (default_user, default_password)
        self.owner_auth = '%s:%s' % (portal_owner, default_password)

        # disable portal_factory as it's a nuisance here
        self.portal.portal_factory.manage_setPortalFactoryTypes(listOfTypeIds=[])

        # object
        self.setupTestObject()

    def setupTestObject(self):
        self.obj_id = 'test_object'
        self.obj = None
        self.obj_url = self.obj.absolute_url()
        self.obj_path = '/%s' % self.obj.absolute_url(1)


class ATCTIntegrationTestCase(IntegrationTestCase):
    """Integration tests for view and edit templates
    """

    portal_type = None

    def setupTestObject(self):
        # create test object
        self.obj_id = 'test_object'
        self.title = u'test \xf6bject'
        self.folder.invokeFactory(self.portal_type, self.obj_id, title=self.title)
        self.obj = getattr(self.folder.aq_explicit, self.obj_id)
        self.obj_url = self.obj.absolute_url()
        self.obj_path = '/%s' % self.obj.absolute_url(1)

    def test_createObject(self):
        # create an object using the createObject script
        response = self.publish(self.folder_path +
                                '/createObject?type_name=%s' % self.portal_type,
                                self.basic_auth)

        self.assertEqual(response.getStatus(), 302)  # Redirect to edit

        body = response.getBody()

        self.assertTrue(body.startswith(self.folder_url), body)
        # The url may end with /edit or /atct_edit depending on method aliases
        self.assertTrue(body.endswith('edit'), body)

        # Perform the redirect
        edit_form_path = body[len(self.app.REQUEST.SERVER_URL):]
        response = self.publish(edit_form_path, self.basic_auth)
        self.assertEqual(response.getStatus(), 200)  # OK
        temp_id = body.split('/')[-2]

        new_obj = getattr(self.folder.portal_factory, temp_id)
        self.assertEqual(self.obj.checkCreationFlag(), True)  # object is not yet edited

    def check_newly_created(self):
        """Objects created programmatically should not have the creation flag set"""
        self.assertEqual(self.obj.checkCreationFlag(), False)  # object is fully created

    def test_edit_view(self):
        # edit should work
        response = self.publish('%s/atct_edit' % self.obj_path, self.basic_auth)
        self.assertEqual(response.getStatus(), 200)  # OK

    def test_base_view(self):
        # base view should work
        response = self.publish('%s/base_view' % self.obj_path, self.basic_auth)
        self.assertEqual(response.getStatus(), 200)  # OK

    def test_dynamic_view(self):
        # dynamic view magic should work
        response = self.publish('%s/view' % self.obj_path, self.basic_auth)
        self.assertEqual(response.getStatus(), 200)  # OK

    def test_local_sharing_view(self):
        # sharing tab should work
        response = self.publish('%s/sharing' % self.obj_path, self.basic_auth)
        self.assertEqual(response.getStatus(), 200)  # OK

    # LinguaPlone specific tests
    if HAS_LINGUA_PLONE:

        def test_linguaplone_views(self):
            response = self.publish('%s/translate_item' % self.obj_path, self.basic_auth)
            self.assertEqual(response.getStatus(), 200)  # OK
            response = self.publish('%s/manage_translations_form' % self.obj_path, self.basic_auth)
            self.assertEqual(response.getStatus(), 200)  # OK

        def test_linguaplone_create_translation(self):
            # create translation creates a new object
            response = self.publish('%s/createTranslation?language=de&set_language=de'
                                     % self.obj_path, self.basic_auth)
            self.assertEqual(response.getStatus(), 302)  # Redirect

            body = response.getBody()
            self.assertTrue(body.startswith(self.folder_url))
            self.assertTrue(body.endswith('/translate_item'))

            # Perform the redirect
            form_path = body[len(self.app.REQUEST.SERVER_URL):]
            response = self.publish(form_path, self.basic_auth)
            self.assertEqual(response.getStatus(), 200)  # OK

            translated_id = "%s-de" % self.obj_id
            self.assertTrue(translated_id in self.folder,
                            self.folder)

    def test_additional_view(self):
        # additional views:
        for view in self.views:
            response = self.publish('%s/%s' % (self.obj_path, view), self.basic_auth)
            self.assertEqual(response.getStatus(), 200,
                "%s: %s" % (view, response.getStatus()))  # OK

    def test_discussion(self):
        # enable discussion for the type
        ttool = getToolByName(self.portal, 'portal_types')
        ttool[self.portal_type].allow_discussion = True

        response = self.publish('%s/discussion_reply_form'
                                 % self.obj_path, self.basic_auth)
        self.assertEqual(response.getStatus(), 200)  # ok

        response = self.publish('%s/discussion_reply?subject=test&body_text=testbody'
                                 % self.obj_path, self.basic_auth)
        self.assertEqual(response.getStatus(), 302)  # Redirect

        body = response.getBody()
        self.assertTrue(body.startswith(self.folder_url))

        self.assertTrue(hasattr(self.obj.aq_explicit, 'talkback'))

        form_path = body[len(self.app.REQUEST.SERVER_URL):]
        discussionId = form_path.split('#')[1]

        reply = self.obj.talkback.getReply(discussionId)
        self.assertEqual(reply.title, 'test')
        self.assertEqual(reply.text, 'testbody')

    def test_dynamicViewContext(self):
        # register and add a testing template (it's a script)
        self.setRoles(['Manager', 'Member'])

        ttool = self.portal.portal_types
        fti = getattr(ttool, self.portal_type)
        view_methods = fti.getAvailableViewMethods(self.obj) + ('unittestGetTitleOf',)
        fti.manage_changeProperties(view_methods=view_methods)

        self.obj.setLayout('unittestGetTitleOf')
        self.folder.setTitle('the folder')
        self.obj.setTitle('the obj')

        self.setRoles(['Member'])

        response = self.publish('%s/view' % self.obj_path, self.basic_auth)
        self.assertEqual(response.getStatus(), 200)  # OK

        output = response.getBody().split(',')
        self.assertEqual(len(output), 4, output)

        self.assertEqual(output, ['the obj', 'the folder', 'the obj', 'the folder'])

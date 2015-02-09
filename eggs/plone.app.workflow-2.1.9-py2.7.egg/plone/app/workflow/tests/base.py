"""Base class for integration tests, based on ZopeTestCase and PloneTestCase.

Note that importing this module has various side-effects: it registers a set of
products with Zope, and it sets up a sandbox Plone site with the appropriate
products installed.
"""

#from Testing import ZopeTestCase

# Import PloneTestCase - this registers more products with Zope as a side effect
from Products.PloneTestCase.PloneTestCase import PloneTestCase
from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
from Products.PloneTestCase.PloneTestCase import setupPloneSite
#from DateTime import DateTime

# Set up a Plone site - note that the portlets branch of CMFPlone applies
# a portlets profile.
setupPloneSite()


class WorkflowTestCase(PloneTestCase):
    """Base class for integration tests for plone.app.workflow. This may
    provide specific set-up and tear-down operations, or provide convenience
    methods.
    """


class WorkflowFunctionalTestCase(FunctionalTestCase):
    """Base class for functional integration tests for plone.app.workflow.
    This may provide specific set-up and tear-down operations, or provide
    convenience methods.
    """

    def afterSetUp(self):

        self.portal.acl_users._doAddUser('manager', 'secret', ['Manager', ], [])
        self.portal.acl_users._doAddUser('member', 'secret', ['Member', ], [])
        self.portal.acl_users._doAddUser('owner', 'secret', ['Owner', ], [])
        self.portal.acl_users._doAddUser('reviewer', 'secret', ['Reviewer', ], [])
        self.portal.acl_users._doAddUser('editor', 'secret', ['Editor', ], [])
        self.portal.acl_users._doAddUser('reader', 'secret', ['Reader', ], [])

        self.portal.acl_users._doAddUser('delegate_reader', 'secret', ['Member', ], [])
        self.portal.acl_users._doAddUser('delegate_editor', 'secret', ['Member', ], [])
        self.portal.acl_users._doAddUser('delegate_contributor', 'secret', ['Member', ], [])
        self.portal.acl_users._doAddUser('delegate_reviewer', 'secret', ['Member', ], [])
        #self.portal.acl_users._doAddUser('delegate_manager', 'secret', ['Member', ], [])

        self.setRoles(('Manager', ))
        self.folder.invokeFactory('News Item', 'newsitem1')
        self.newsitem = self.folder.newsitem1
        self.folder.invokeFactory('Event', 'event1')
        self.event = self.folder.event1
        self.folder.invokeFactory('Document', 'document1')
        self.document = self.folder.document1
        self.setRoles(('Member', ))

    def setUpDefaultWorkflow(self, defaultWorkflow=None, hasFolderSpecificWorkflow=False):
        # XXX - TODO: we'll be able to replace this all with the new remap template
        self.workflow = self.portal.portal_workflow
        ctypes = self.portal.allowedContentTypes()
        # XXX figure out the real way to get the types
        ctypes = ('Document', 'Folder', 'News Item', 'Event', )

        for ctype in ctypes:
            if ctype in ('Folder', 'Smart Folder') and hasFolderSpecificWorkflow:
                # XXX factor in *_folder_* workflow declarations
                self.workflow.setChainForPortalTypes(('%s' % ctype, ), ('%s' % defaultWorkflow, ))
            else:
                self.workflow.setChainForPortalTypes(('%s' % ctype, ), ('%s' % defaultWorkflow, ))

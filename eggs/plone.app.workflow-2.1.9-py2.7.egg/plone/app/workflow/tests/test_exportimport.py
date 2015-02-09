import unittest
from zope.interface import Interface
from zope.component import provideAdapter, provideUtility, getUtilitiesFor, getSiteManager
from zope.component.testing import tearDown

from five.localsitemanager import make_objectmanager_site
from zope.site.hooks import setHooks, setSite, clearSite

from plone.app.workflow.exportimport import import_sharing, export_sharing
from plone.app.workflow.exportimport import SharingXMLAdapter
from plone.app.workflow.exportimport import PersistentSharingPageRole

from plone.app.workflow.interfaces import ISharingPageRole

from Products.GenericSetup.tests.common import DummyImportContext
from Products.GenericSetup.tests.common import DummyExportContext

from OFS.Folder import Folder


class ExportImportTest(unittest.TestCase):

    def setUp(self):
        provideAdapter(SharingXMLAdapter, name='plone.app.workflow.sharing')

        site = Folder('plone')
        make_objectmanager_site(site)
        setHooks()
        setSite(site)
        sm = getSiteManager()

        self.site = site
        self.sm = sm

    def roles(self):
        return dict(getUtilitiesFor(ISharingPageRole))

    def tearDown(self):
        clearSite()
        tearDown()


class TestImport(ExportImportTest):

    def test_empty_import_no_purge(self):

        xml = "<sharing />"
        context = DummyImportContext(self.site, purge=False)
        context._files = {'sharing.xml': xml}

        import_sharing(context)

        self.assertEquals(0, len(self.roles()))

    def test_import_single_no_purge(self):

        xml = """\
<sharing>
    <role id='CopyEditor'
          title='Can copyedit'
          permission='Delegate edit copy'
          interface='zope.interface.Interface' />
</sharing>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'sharing.xml': xml}

        import_sharing(context)
        roles = self.roles()

        self.assertEquals(1, len(roles))

        self.assertEquals('Can copyedit', roles['CopyEditor'].title)
        self.assertEquals('Delegate edit copy', roles['CopyEditor'].required_permission)
        self.assertEquals(Interface, roles['CopyEditor'].required_interface)

    def test_import_multiple_no_purge(self):

        xml = """\
<sharing>
    <role id='CopyEditor'
          title='Can copyedit'
          permission='Delegate edit copy'
          interface='zope.interface.Interface' />
    <role id='Controller'
          title='Can control' />
</sharing>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'sharing.xml': xml}

        import_sharing(context)
        roles = self.roles()

        self.assertEquals(2, len(roles))
        self.assertEquals('Can copyedit', roles['CopyEditor'].title)
        self.assertEquals('Delegate edit copy', roles['CopyEditor'].required_permission)
        self.assertEquals(Interface, roles['CopyEditor'].required_interface)
        self.assertEquals('Can control', roles['Controller'].title)
        self.assertEquals(None, roles['Controller'].required_permission)

    def test_import_multiple_times_no_purge(self):

        xml = """\
<sharing>
    <role id='CopyEditor'
          title='Can copyedit'
          permission='Delegate edit copy'
          interface='zope.interface.Interface' />
</sharing>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'sharing.xml': xml}

        import_sharing(context)
        roles = self.roles()

        self.assertEquals(1, len(roles))
        self.assertEquals('Can copyedit', roles['CopyEditor'].title)
        self.assertEquals('Delegate edit copy', roles['CopyEditor'].required_permission)
        self.assertEquals(Interface, roles['CopyEditor'].required_interface)

        xml = """\
<sharing>
    <role id='Controller'
          title='Can control' />
</sharing>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'sharing.xml': xml}

        import_sharing(context)
        roles = self.roles()

        self.assertEquals(2, len(roles))
        self.assertEquals('Can copyedit', roles['CopyEditor'].title)
        self.assertEquals('Delegate edit copy', roles['CopyEditor'].required_permission)
        self.assertEquals(Interface, roles['CopyEditor'].required_interface)
        self.assertEquals('Can control', roles['Controller'].title)
        self.assertEquals(None, roles['Controller'].required_permission)

    def test_import_multiples_times_purge(self):

        xml = """\
<sharing>
    <role id='CopyEditor'
          title='Can copyedit'
          permission='Delegate edit copy'
          interface='zope.interface.Interface' />
</sharing>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'sharing.xml': xml}

        import_sharing(context)
        roles = self.roles()

        self.assertEquals(1, len(roles))
        self.assertEquals('Can copyedit', roles['CopyEditor'].title)
        self.assertEquals('Delegate edit copy', roles['CopyEditor'].required_permission)
        self.assertEquals(Interface, roles['CopyEditor'].required_interface)

        xml = """\
<sharing>
    <role id='Controller'
          title='Can control' />
</sharing>
"""
        context = DummyImportContext(self.site, purge=True)
        context._files = {'sharing.xml': xml}

        import_sharing(context)
        roles = self.roles()

        self.assertEquals(1, len(roles))
        self.assertEquals('Can control', roles['Controller'].title)
        self.assertEquals(None, roles['Controller'].required_permission)

    def test_import_multiples_times_no_purge_overwrite(self):

        xml = """\
<sharing>
    <role id='CopyEditor'
          title='Can copyedit'
          permission='Delegate edit copy'
          interface='zope.interface.Interface' />
</sharing>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'sharing.xml': xml}

        import_sharing(context)
        roles = self.roles()

        self.assertEquals(1, len(roles))
        self.assertEquals('Can copyedit', roles['CopyEditor'].title)
        self.assertEquals('Delegate edit copy', roles['CopyEditor'].required_permission)
        self.assertEquals(Interface, roles['CopyEditor'].required_interface)

        xml = """\
<sharing>
    <role id='CopyEditor'
          title='Can edit copy'
          permission='Delegate: CopyEditor' />
</sharing>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'sharing.xml': xml}

        import_sharing(context)
        roles = self.roles()

        self.assertEquals(1, len(roles))
        self.assertEquals('Can edit copy', roles['CopyEditor'].title)
        self.assertEquals('Delegate: CopyEditor', roles['CopyEditor'].required_permission)
        self.assertEquals(None, roles['CopyEditor'].required_interface)

    def test_import_override_global(self):

        provideUtility(PersistentSharingPageRole("Do stuff", "A permission"), ISharingPageRole, name="DoerOfStuff")

        xml = """\
<sharing>
    <role id='CopyEditor'
          title='Can copyedit'
          permission='Delegate edit copy' />
    <role id='DoerOfStuff'
          title='Can do stuff'
          permission='Delegate doing stuff' />
</sharing>
"""
        context = DummyImportContext(self.site, purge=False)
        context._files = {'sharing.xml': xml}

        import_sharing(context)
        roles = self.roles()

        self.assertEquals(2, len(roles))
        self.assertEquals('Can copyedit', roles['CopyEditor'].title)
        self.assertEquals('Delegate edit copy', roles['CopyEditor'].required_permission)
        self.assertEquals(None, roles['CopyEditor'].required_interface)
        self.assertEquals('Can do stuff', roles['DoerOfStuff'].title)
        self.assertEquals('Delegate doing stuff', roles['DoerOfStuff'].required_permission)

    def test_remove_one(self):

        xml = """\
<sharing>
    <role id='CopyEditor'
          title='Can copyedit'
          permission='Delegate edit copy' />
</sharing>
"""
        context = DummyImportContext(self.sm, purge=False)
        context._files = {'sharing.xml': xml}

        import_sharing(context)
        roles = self.roles()

        self.assertEquals(1, len(roles))
        self.assertEquals('Can copyedit', roles['CopyEditor'].title)

        xml = """\
<sharing>
    <role remove="True"
          id='CopyEditor' />
</sharing>
"""
        context = DummyImportContext(self.sm, purge=False)
        context._files = {'sharing.xml': xml}

        import_sharing(context)
        roles = self.roles()

        self.assertEquals(0, len(roles))

    def test_remove_multiple(self):
        xml = """\
<sharing>
    <role id='CopyEditor'
          title='Can copyedit'
          permission='Delegate edit copy' />
    <role id='DoerOfStuff'
          title='Can do stuff'
          permission='Delegate doing stuff' />
</sharing>
"""
        context = DummyImportContext(self.sm, purge=False)
        context._files = {'sharing.xml': xml}
        import_sharing(context)

        xml = """\
<sharing>
    <role id='Hacker'
          title='Can hack'
          permission='Hack the system' />
    <role remove="True"
          id='CopyEditor'
          title='Can copyedit'
          permission='Delegate edit copy' />
</sharing>
"""
        context = DummyImportContext(self.sm, purge=False)
        context._files = {'sharing.xml': xml}

        import_sharing(context)
        roles = self.roles()

        self.assertEquals(2, len(roles))
        self.assertEquals('Can do stuff', roles['DoerOfStuff'].title)
        self.assertEquals('Can hack', roles['Hacker'].title)


class TestExport(ExportImportTest):

    def test_export_empty(self):

        xml = """\
<?xml version="1.0"?>
<sharing/>
"""
        context = DummyExportContext(self.site)
        export_sharing(context)

        self.assertEquals('sharing.xml', context._wrote[0][0])
        self.assertEquals(xml, context._wrote[0][1])

    def test_export_multiple(self):
        sm = self.site.getSiteManager()

        # Will not be exported, as it's global
        provideUtility(PersistentSharingPageRole("Do stuff", "A permission"), ISharingPageRole, name="DoerOfStuff")

        # Will not be exported, as it wasn't imported with this handler
        sm.registerUtility(PersistentSharingPageRole("Do other Stuff"), ISharingPageRole, "DoerOfOtherStuff")

        import_xml = """\
<sharing>
 <role title="Can control" id="Controller"/>
 <role title="Can copyedit" id="CopyEditor"
    interface="zope.interface.Interface" permission="Delegate edit copy"/>
</sharing>
"""

        export_xml = """\
<?xml version="1.0"?>
<sharing>
 <role title="Can control" id="Controller"/>
 <role title="Can copyedit" id="CopyEditor"
    interface="zope.interface.Interface" permission="Delegate edit copy"/>
</sharing>
"""

        import_context = DummyImportContext(self.site, purge=False)
        import_context._files = {'sharing.xml': import_xml}

        import_sharing(import_context)

        export_context = DummyExportContext(self.site)
        export_sharing(export_context)

        self.assertEquals('sharing.xml', export_context._wrote[0][0])

        self.assertEquals(export_xml, export_context._wrote[0][1])


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)

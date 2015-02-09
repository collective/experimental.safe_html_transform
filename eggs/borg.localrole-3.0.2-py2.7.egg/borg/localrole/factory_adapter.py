from zope.component import adapts
from zope.interface import implements
from borg.localrole.interfaces import IFactoryTempFolder
from borg.localrole.interfaces import ILocalRoleProvider
from Acquisition import aq_inner, aq_parent
from Products.CMFCore.utils import getToolByName

class FactoryTempFolderProvider(object):
    """A simple local role provider which just gathers the roles from
    the desired context::

        >>> from Testing.ZopeTestCase import placeless
        >>> placeless.setUp()
        >>> from zope.component import provideAdapter
        >>> from zope.interface import Interface, implements, directlyProvides
        >>> from borg.localrole.workspace import WorkspaceLocalRoleManager
        >>> rm = WorkspaceLocalRoleManager('rm', 'A Role Manager')

        >>> from Acquisition import Implicit
        >>> class DummyObject(Implicit):
        ...     implements(Interface)
        >>> root = DummyObject()


    Let's construct a hierarchy similar to the way portal factory is used::

        root --> folder -------|
          |------------> PortalFactory --> TempFolder --> NewObject

        >>> fold = DummyObject().__of__(root)
        >>> factory = DummyObject().__of__(root)
        >>> wrapped_factory = factory.__of__(fold)
        >>> temp = DummyObject().__of__(wrapped_factory)
        >>> newob = DummyObject().__of__(temp)

        >>> from borg.localrole.tests import SimpleLocalRoleProvider
        >>> from borg.localrole.tests import DummyUser
        >>> user1 = DummyUser('bogus_user1')


    To test our adapter we need an acl_users, and our user needs a
    getRolesInContext method::

        >>> class FakeUF(object):
        ...     def getUserById(self, userid, default=None):
        ...         if userid == user1.getId():
        ...             return user1
        ...         return None
        >>> root.acl_users = FakeUF()

        >>> def getRolesInContext(user, context):
        ...     return rm.getRolesInContext(user, context)
        >>> from new import instancemethod
        >>> user1.getRolesInContext = instancemethod(getRolesInContext, user1,
        ...                                          DummyUser)


    We add special interface to our Folder which allows us to provide
    some local roles, these roles will be inherited by any contained
    objects but not by our 'newob' because though the folder is its
    acquisition chain it is not contained by it::

        >>> class ISpecialInterface(Interface):
        ...     pass
        >>> directlyProvides(fold, ISpecialInterface)
        >>> provideAdapter(SimpleLocalRoleProvider, adapts=(ISpecialInterface,))
        >>> rm.getRolesInContext(user1, fold)
        ['Foo']
        >>> contained = DummyObject().__of__(fold)
        >>> rm.getRolesInContext(user1, contained)
        ['Foo']
        >>> rm.getRolesInContext(user1, newob)
        []

    Now we mark our TempFolder, and check that roles are now inherited
    from the intended location ('fold')::

        >>> directlyProvides(temp, IFactoryTempFolder)
        >>> provideAdapter(FactoryTempFolderProvider)
        >>> rm.getRolesInContext(user1, newob)
        ['Foo']

    The getAllRoles method always returns an empty dict, becuas it is
    only used for thing which are irrelevant for temporary objects::

        >>> rm.getAllLocalRolesInContext(newob)
        {}


        >>> placeless.tearDown()

    """
    adapts(IFactoryTempFolder)
    implements(ILocalRoleProvider)

    def __init__(self, obj):
        self.folder = obj

    def getRoles(self, principal_id):
        uf = aq_inner(getToolByName(self.folder, 'acl_users'))
        user = aq_inner(uf.getUserById(principal_id, default=None))
        # use the folder we are creating in as role generating context
        source = aq_parent(aq_parent(self.folder))
        if user is not None:
            return user.getRolesInContext(source)
        else:
            return []

    def getAllRoles(self):
        # This should not be used in any meaningful way, so we'll make it cheap
        return {}

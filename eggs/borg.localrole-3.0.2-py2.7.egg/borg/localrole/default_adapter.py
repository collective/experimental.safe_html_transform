from zope.interface import Interface, implements
from zope.component import adapts
from borg.localrole.interfaces import ILocalRoleProvider


class DefaultLocalRoleAdapter(object):
    """Looks at __ac_local_roles__ to find local roles stored
    persistently on an object::

        >>> class Dummy(object):
        ...     pass
        >>> obj = Dummy()
        >>> roles = DefaultLocalRoleAdapter(obj)


    Let's make sure the behavior is sane for objects with no local
    role awareness::

        >>> roles.getRoles('dummy')
        []
        >>> tuple(roles.getAllRoles())
        ()

    Same goes if the RoleManager role map is set to None::

        >>> obj.__ac_local_roles__ = None
        >>> roles.getRoles('dummy')
        []
        >>> tuple(roles.getAllRoles())
        ()

    And if we have some roles assigned, we get the expected behavior::

        >>> obj.__ac_local_roles__ = {'dummy': ['Role1', 'Role2']}
        >>> roles.getRoles('dummy')
        ['Role1', 'Role2']
        >>> roles.getRoles('dummy2')
        []
        >>> tuple(roles.getAllRoles())
        (('dummy', ['Role1', 'Role2']),)

    The __ac__local_roles__ attribute may be a callable::

        >>> obj.__ac_local_roles__ = lambda: {'dummy2': ['Role1']}
        >>> roles.getRoles('dummy')
        []
        >>> roles.getRoles('dummy2')
        ['Role1']
        >>> tuple(roles.getAllRoles())
        (('dummy2', ['Role1']),)

    """
    implements(ILocalRoleProvider)
    adapts(Interface)

    def __init__(self, context):
        self.context = context

    @property
    def _rolemap(self):
        rolemap = getattr(self.context, '__ac_local_roles__', {})
        # None is the default value from AccessControl.Role.RoleMananger
        if rolemap is None:
            return {}
        if callable(rolemap):
            rolemap = rolemap()
        return rolemap

    def getRoles(self, principal_id):
        """Returns the roles for the given principal in context"""
        return self._rolemap.get(principal_id, [])

    def getAllRoles(self):
        """Returns all the local roles assigned in this context:
        (principal_id, [role1, role2])"""
        return self._rolemap.iteritems()

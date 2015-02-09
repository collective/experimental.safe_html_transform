from zope.interface import Interface

# BBB: These interfaces will be removed in a later version of borg.locarole.
# You should use the interfaces in borg.localrole.interfaces instead!


class IWorkspace(Interface):
    """A workspace in which custom local roles are needed

    A workspace gives information to the Pluggable Authentication Service
    about local roles. The context will be adapted to this interface to
    find out which additional local roles should apply.
    """

    def getLocalRolesForPrincipal(principal):
        """Return a sequence of all local roles for a principal.
        """

    def getLocalRoles():
        """Return a dictonary mapping principals to their roles within
        a workspace.
        """


class IGroupAwareWorkspace(IWorkspace):
    """A group-aware version of IWorkspace.

    This should ensure that getLocalRolesForPrincipal() and getLocalRoles()
    return values for principals which are groups as well as principals
    which are users.

    Supporting only IWorkspace instead of IGroupAwareWorkspace will mean a
    slight performance increase, since there is no need to look up and
    iterate over groups.
    """

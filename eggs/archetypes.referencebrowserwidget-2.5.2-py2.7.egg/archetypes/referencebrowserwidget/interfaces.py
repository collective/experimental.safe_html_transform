from zope.interface import Interface
from Products.Archetypes.interfaces import IObjectField


class IFieldRelation(Interface):
    """ """


class IATReferenceField(IObjectField):
    """ Missing marker for Products.Archetypes.Field.ReferenceField """


class IATBackRefereneceField(IObjectField):
    """ Missing marker for Products.ATBackRef.BackReferenceField """


class IPloneRelationsRefField(IObjectField):
    """ Missing marker for plone.relations.PloneRelationsATField """


class IPloneRelationsRevRefField(IObjectField):
    """ Missing marker for plone.relations.ReversePloneRelationsATField """


class IReferenceBrowserHelperView(Interface):

    def getFieldRelations(field, value):
        """ """

    def getStartupDirectory(field):
        """ """

    def getUidFromReference(ref):
        """ Get UID in restricted code

            Can be used in restricted code without having rights to
            access the object.
        """

    def getPortalPath():
        """ Return the path to the portal """

    def canView(obj):
        """ Check, if the logged in user has the view permission on `obj` """

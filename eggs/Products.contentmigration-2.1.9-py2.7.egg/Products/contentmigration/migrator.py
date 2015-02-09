from Acquisition import aq_inner
from field import migrateField


class BaseInlineMigrator(object):
    """This migrator base class is similar to the ATContentTypes BaseMigrator,
    except it is designed to migrate fields within the same content type,
    not across types. To that end, it does not do a rename-copy-create cycle,
    it simply operates on the objects the walker returns.

    The base class has the following attributes:

     * portal_type
       The portal type name the migration is migrating *from*
       Can be overwritten in the constructor
     * meta_type
       The meta type of the src object
     * obj
       The object being migrated
     * kwargs
       A dict of additional keyword arguments applied to the migrator
    """
    portal_type = None
    meta_type = None
    kwargs = {}

    # Framework requires us to have dst_ versions, even if they are not
    # used
    dst_portal_type = dst_meta_type = '__dummy__'

    def __init__(self, obj, portal_type=None, meta_type=None, **kwargs):
        self.obj = aq_inner(obj)
        if portal_type is not None:
            self.portal_type = portal_type
        if meta_type is not None:
            self.meta_type = meta_type
        self.kwargs = kwargs

    def getMigrationMethods(self):
        """Calculates a nested list of callables used to migrate the old object
        """
        beforeChange = []
        methods      = []
        lastmethods  = []
        for name in dir(self):
            if name.startswith('beforeChange_'):
                method = getattr(self, name)
                if callable(method):
                    beforeChange.append(method)
            if name.startswith('migrate_'):
                method = getattr(self, name)
                if callable(method):
                    methods.append(method)
            if name.startswith('last_migrate_'):
                method = getattr(self, name)
                if callable(method):
                    lastmethods.append(method)

        afterChange = methods+[self.custom]+lastmethods
        return (beforeChange, afterChange, )

    def migrate(self):
        """Migrates the object
        """
        beforeChange, afterChange = self.getMigrationMethods()

        for method in beforeChange:
            __traceback_info__ = (self, method, self.obj)
            method()

        for method in afterChange:
            __traceback_info__ = (self, method, self.obj)
            method()

    __call__ = migrate

    def custom(self):
        """Override this to provide custom migration.
        """
        pass

class InlineFieldActionMigrator(BaseInlineMigrator):
    """Mixin class to enable field migrations based on field migration actions.
    This allows migrating of attributes using declarative actions. It works
    on an Archetypes storage level, which means that it's capable of migrating
    attributes when interfaces have changed. It also allows you to migrate
    between different implementations of the same content type, by setting the
    src_- and dest_- portal- and meta- types to the same type.

    To use it, you should set the class variable fieldActions to a list of dicts
    specifying field actions. To see how these work, please look at field.py.

    If you specify field actions, it's probably best not to use the 'map'
    migrator feature for any of these fields.
    """

    fieldActions = ()

    def migrate_withFieldActions(self):
        """Apply field migration actions"""
        for action in self.fieldActions:
            migrateField(obj = self.obj, action = action, **self.kwargs)


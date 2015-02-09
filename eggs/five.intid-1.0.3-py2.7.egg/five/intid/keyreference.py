from Acquisition import aq_base, aq_chain, IAcquirer
from ZODB.interfaces import IConnection
from ZPublisher.BaseRequest import RequestContainer
from zExceptions import NotFound
from persistent import IPersistent
from zope.component import adapter, adapts
from zope.site.hooks import getSite
from zope.interface import implements, implementer
from zope.keyreference.interfaces import IKeyReference, NotYet
from zope.keyreference.persistent import KeyReferenceToPersistent
from site import get_root, aq_iter
from zope.lifecycleevent.interfaces import IObjectAddedEvent


@adapter(IPersistent)
@implementer(IConnection)
def connectionOfPersistent(obj):
    """ zope2 cxn fetcher for wrapped items """
    if not (IAcquirer.providedBy(obj) or hasattr(obj, '__parent__')):
        return getattr(obj, '_p_jar', None)

    for parent in aq_iter(obj):
        conn = getattr(parent, '_p_jar', None)
        if conn is not None:
            return conn


@adapter(IPersistent, IObjectAddedEvent)
def add_object_to_connection(ob, event):
    """Pre-add new objects to their persistence connection"""
    connection = IConnection(ob, None)
    if None is not connection:
        connection.add(aq_base(ob))


class KeyReferenceToPersistent(KeyReferenceToPersistent):
    """a zope2ish implementation of keyreferences that unwraps objects
    that have Acquisition wrappers

    These references compare by _p_oids of the objects they reference.

    @@ cache IConnection as a property and volative attr?
    """
    implements(IKeyReference)
    adapts(IPersistent)

    key_type_id = 'five.intid.keyreference'
    # Default dbname where the root is. This is defined here for
    # backward compatibility with previously created objects.
    root_dbname = 'main'

    def __init__(self, wrapped_obj):

        # Detect a circular containment / an infinite Loop with aq_iter
        try:
            [obj for obj in aq_iter(wrapped_obj, error=RuntimeError)]
        except RuntimeError:
            raise NotYet(wrapped_obj)

        # make sure our object is wrapped by containment only
        try:
            self.path = '/'.join(wrapped_obj.getPhysicalPath())
        except AttributeError:
            self.path = None

        # If the path ends with /, it means the object had an empty id.
        # This means it's not yet added to the container, and so we have
        # to defer.
        if self.path is not None and self.path.endswith('/'):
            raise NotYet(wrapped_obj)
        self.object = aq_base(wrapped_obj)
        connection = IConnection(wrapped_obj, None)

        if not getattr(self.object, '_p_oid', None):
            if connection is None:
                raise NotYet(wrapped_obj)
            connection.add(self.object)

        try:
            root = get_root(wrapped_obj)
        except AttributeError:
            # If the object is unwrapped we can try to use the Site from the
            # threadlocal as our acquisition context, hopefully it's not
            # something odd.
            root = get_root(getSite())
        self.root_oid = root._p_oid
        self.root_dbname = IConnection(root).db().database_name
        self.oid = self.object._p_oid
        self.dbname = connection.db().database_name

    @property
    def root(self):
        # It is possible that the root is not in the same db that the
        # object. Asking the root object on the wrong db can trigger
        # an POSKeyError.
        connection = IConnection(self.object).get_connection(self.root_dbname)
        return connection[self.root_oid]

    @property
    def wrapped_object(self):
        if self.path is None:
            return self.object
        try:
            obj = self.root.unrestrictedTraverse(self.path)
        except (NotFound, AttributeError,):
            return self.object
        chain = aq_chain(obj)
        # Try to ensure we have a request at the acquisition root
        # by using the one from getSite
        if not len(chain) or not isinstance(chain[-1], RequestContainer):
            site = getSite()
            site_chain = aq_chain(site)
            if len(site_chain) and isinstance(site_chain[-1],
                                              RequestContainer):
                req = site_chain[-1]
                new_obj = req
                # rebuld the chain with the request at the bottom
                for item in reversed(chain):
                    new_obj = aq_base(item).__of__(new_obj)
                obj = new_obj
        return obj

    def __call__(self):
        return self.wrapped_object

    def __hash__(self):
        return hash((self.dbname,
                     self.object._p_oid,
                     ))

    def __cmp__(self, other):
        if self.key_type_id == other.key_type_id:
            return cmp((self.dbname,self.oid), (other.dbname, other.oid))
        return cmp(self.key_type_id, other.key_type_id)

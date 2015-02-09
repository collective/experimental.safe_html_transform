from Missing import Value as MissingValue
from Products.Archetypes.interfaces import IReferenceable
from Products.CMFCore.utils import getToolByName
from wicked.interfaces import IWickedFilter, IWickedTarget
from wicked.at import config
from wicked.interfaces import IATBacklinkManager, IUID
from wicked.normalize import titleToNormalizedId as normalize
from relation import Backlink
from zope.interface import alsoProvides as mark
from zope.interface import implements
from wicked.utils import packBrain, cleanUID
from zope.component import adapts


class ATBacklinkManager(object):
    #@@ needs refactoring
    implements(IATBacklinkManager)
    adapts(IWickedFilter, IReferenceable)

    relation = config.BACKLINK_RELATIONSHIP
    refKlass = Backlink

    packBrain = staticmethod(packBrain)

    def __init__(self, wfilter, context):
        self.wfilter = wfilter
        self.context = context
        self.cm = wfilter.cache
        self.resolver = wfilter.resolver
        self.getMatch = wfilter.getMatch
        ## ATism: remove ASAP
        self.refcat = getToolByName(self.context, 'reference_catalog')
        self.suid = IUID(self.context)

    def getLinks(self):
        """
        Returns dataobjects representing backlinks
        """
        refbrains = self.refcat._queryFor(relationship=self.relation,
                                 tid=self.suid, sid=None)
        if refbrains:
            uids = [brain.sourceUID for brain in refbrains]
            ## XXX non-orthogonal
            return self.resolver.queryUIDs(uids)
        return []

    def _preplinks(self, links=dict()):
        return links and dict([(normalize(link), link) for link in links]) \
                     or dict()

    def manageLinks(self, new_links):
        # this has been heavily optimized
        # @@ but asyncing backlinking would help

        scope=self.wfilter.scope
        dups = set(self.removeLinks(new_links))

        resolver = self.resolver
        norm=tuple()
        for link in new_links:
            normalled=normalize(link)
            norm+=normalled,
            self.resolver.aggregate(link, normalled, scope)

        for link, normalled in zip(new_links, norm):
            match = self.getMatch(link, resolver.agg_brains, normalled=normalled)
            if not match:
                match = self.getMatch(link, resolver.agg_scoped_brains, normalled=normalled)
            if not match:
                continue
            if match.UID != MissingValue and match.UID in dups:
                continue
            self.manageLink(match, normalled)

    def manageLink(self, obj, normalled):
        # need IObject iface for catalog brains
        if hasattr(obj, 'getObject'):
            # brain, other sort of pseudo object
            obj = obj.getObject()

        if not IReferenceable.providedBy(obj):
            # backlink not possible
            return

        mark(obj, IWickedTarget)
        self.refcat.addReference(obj,
                                 self.context,
                                 relationship=self.relation,
                                 referenceClass=self.refKlass)
        objuid = IUID(obj)
        path = '/'.join(obj.getPhysicalPath())
        data = dict(path=path,
                    icon=obj.getIcon(),
                    uid=objuid)

        self.cm.set((intern(str(normalled)), objuid), [data])

    def removeLinks(self, exclude=tuple()):
        oldlinks = self.getLinks()
        if not oldlinks:
            return set()

        exclude = self._preplinks(exclude)
        dups = set([brain for brain in oldlinks if \
                    self.match(brain, exclude.get)])

        [self.remove(brain) for brain in set(oldlinks) - dups]
        return [self.cleanUID(b) for b in dups]

    cleanUID = staticmethod(cleanUID)

    def match(self, brain, getlink):
        """
        mmmm....turtle.
        @@ make efficient
        """
        link = getlink(brain.getId,
                       getlink(normalize(brain.Title), None))
        if link:
            return True

    def remove(self, brain):
        #XXX needs test
        objs = self.refcat._resolveBrains(\
            self.refcat._queryFor(self.suid, brain.UID, self.relation))
        for obj in objs:
            self.refcat._deleteReference(obj)
            self.cm.unset(obj.targetUID, use_uid=True)

    def unlink(self, uid):
        self.cm.remove(uid)

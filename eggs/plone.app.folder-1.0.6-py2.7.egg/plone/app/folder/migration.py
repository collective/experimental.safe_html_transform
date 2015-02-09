from logging import getLogger
from time import clock, strftime
from Acquisition import aq_base
from Products.Five.browser import BrowserView
from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2Base as BTreeFolder
from plone.app.folder.utils import findObjects, timer, checkpointIterator
from transaction import get

logger = getLogger(__name__)


class BTreeMigrationView(BrowserView):
    """ helper view for btree-migration;  all old-style folder, which
        are btree-based now (implementation-wise) will be migration
        in term of their internal data structures being updated """

    def mklog(self):
        """ helper to prepend a time stamp to the output """
        write = self.request.RESPONSE.write
        def log(msg, timestamp=True, cr=True):
            if timestamp:
                msg = strftime('%Y/%m/%d-%H:%M:%S ') + msg
            if cr:
                msg += '\n'
            write(msg)
        return log

    def migrate(self, folder):
        """ migrate existing data structure from a regular folder to a btree
            folder;  the folder needs to be btree-based already """
        folder = aq_base(folder)
        assert isinstance(folder, BTreeFolder)
        assert folder.getId()       # make sure the object is properly loaded
        has = folder.__dict__.has_key
        if has('_tree') and not has('_objects'):
            return False            # already migrated...
        folder._initBTrees()        # create _tree, _count, _mt_index
        for info in folder._objects:
            name = info['id']
            # _setOb will notify the ordering adapter itself,
            # so we don't need to care about storing order information here...
            folder._setOb(name, aq_base(getattr(folder, name)))
            delattr(folder, name)
        if has('_objects'):
            delattr(folder, '_objects')
        return True

    def postprocess(self, obj):
        # This is a hook for other migration code and is used in
        # plone.app.upgrade
        pass

    def __call__(self, batch=1000, dryrun=False):
        """ find all btree-based folder below the context, potentially
            migrate them & provide some logging and statistics doing so """
        log = self.mklog()
        log('migrating btree-based folders from %r:' % self.context)
        real = timer()          # real time
        lap = timer()           # real lap time (for intermediate commits)
        cpu = timer(clock)      # cpu time
        processed = 0
        def checkPoint():
            msg = 'intermediate commit (%d objects processed, last batch in %s)...'
            log(msg % (processed, lap.next()))
            trx = get()
            trx.note('migrated %d btree-folders' % processed)
            trx.savepoint()
        cpi = checkpointIterator(checkPoint, batch)
        for path, obj in findObjects(self.context):
            if isinstance(obj, BTreeFolder):
                if self.migrate(obj):
                    processed += 1
                    cpi.next()
            self.postprocess(obj)

        checkPoint()                # commit last batch
        if dryrun:
            get().abort()           # abort on test-run...
        msg = 'processed %d object(s) in %s (%s cpu time).'
        msg = msg % (processed, real.next(), cpu.next())
        log(msg)
        logger.info(msg)

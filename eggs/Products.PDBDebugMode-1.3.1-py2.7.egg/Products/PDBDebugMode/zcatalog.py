"""Monkey patches to various ZCatalog code that swallows errors we
might want to debug."""

import sys
try:
    import ipdb as pdb
except:
    import pdb

from Products.ZCatalog.ZCatalog import ZCatalog

orig_catalog_object = ZCatalog.catalog_object

def catalog_object(self, obj, uid=None, idxs=None,
                    update_metadata=1, pghandler=None):
    """Wrap to do post_mortem debugging on error."""
    try:
        return orig_catalog_object(
            self, obj, uid=uid, idxs=idxs,
            update_metadata=update_metadata, pghandler=pghandler)
    except:
        t, v, tb = sys.exc_info()
        pdb.post_mortem(tb)
        raise

def refreshCatalog(self, clear=0, pghandler=None):
    """Don't swallow errors on object indexing errors."""

    cat = self._catalog
    paths = cat.paths.values()
    if clear:
        paths = tuple(paths)
        cat.clear()

    num_objects = len(paths)
    if pghandler:
        pghandler.init('Refreshing catalog: %s' % self.absolute_url(1), num_objects)

    for i in xrange(num_objects):
        if pghandler: pghandler.report(i)

        p = paths[i]
        obj = self.resolve_path(p)
        if not obj:
            obj = self.resolve_url(p, self.REQUEST)
        if obj is not None:
            self.catalog_object(obj, p, pghandler=pghandler)

    if pghandler: pghandler.finish()

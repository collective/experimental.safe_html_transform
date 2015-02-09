try:
    import ipdb as pdb
except:
    import pdb

from Products.SiteErrorLog import SiteErrorLog

from Products.PDBDebugMode import pdblogging

orig_raising = SiteErrorLog.SiteErrorLog.raising

def raising(self, info):
    """Catch the traceback and bypass pdblogging"""
    def error(msg, *args, **kw):
        return pdblogging.orig_error(
            SiteErrorLog.LOG, msg, *args, **kw)
    SiteErrorLog.LOG.error = error
    result = orig_raising(self, info)
    if result:
        pdb.post_mortem(info[2])
    del SiteErrorLog.LOG.error
    return result

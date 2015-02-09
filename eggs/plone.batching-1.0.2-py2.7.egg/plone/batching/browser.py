from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from ZTUtils import  make_query

BatchTemplate = ViewPageTemplateFile("batchnavigation.pt")
BootstrapBatchTemplate = ViewPageTemplateFile("batchnavigation_bootstrap.pt")

class BatchMacrosView(BrowserView):
    @property
    def macros(self):
        return self.template.macros


class BatchView(BrowserView):
    """ View class for browser navigation  (classic) """

    index = BatchTemplate
    batch = None
    batchformkeys = None
    minimal_navigation = False

    def __call__(self, batch, batchformkeys=None, minimal_navigation=False):
        self.batch = batch
        self.batchformkeys = batchformkeys
        self.minimal_navigation = minimal_navigation
        return self.index()

    def make_link(self, pagenumber):
        raise NotImplementedError


class BootstrapBatchView(BatchView):
    index = BootstrapBatchTemplate


class PloneBatchView(BatchView):
    def make_link(self, pagenumber=None):
        form = self.request.form
        if self.batchformkeys:
            batchlinkparams = dict([(key, form[key])
                                    for key in self.batchformkeys
                                    if key in form])
        else:
            batchlinkparams = form.copy()

        start = max(pagenumber - 1, 0) * self.batch.pagesize
        return '%s?%s' % (self.request.ACTUAL_URL, make_query(batchlinkparams,
                         {self.batch.b_start_str: start}))


class PloneBootstrapBatchView(BootstrapBatchView, PloneBatchView):
    pass

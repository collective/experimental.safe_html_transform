from Products.Five.browser import BrowserView

class RaiseExceptionView(BrowserView):
    def __call__(self):
        raise Exception, "Manually triggered exception"

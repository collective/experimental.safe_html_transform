import json

from zope.formlib import form as formlib

from Acquisition import aq_inner
from Products.Five import BrowserView
from Products.Five.browser.decode import processInputs
from Products.Five.browser.decode import setPageEncoding


class InlineValidationView(BrowserView):
    """Validate a form and return the error message for a particular field as JSON.
    """

    def __call__(self, fname):
        res = {'errmsg': ''}

        form = aq_inner(self.context)
        context = aq_inner(form.context)
        request = self.request
        processInputs(request)
        setPageEncoding(request)

        raw_fname = fname[len(form.prefix) + 1:]
        formlib_field = form.form_fields[raw_fname]
 
        widgets = formlib.setUpWidgets(
            (formlib_field,), form.prefix, context,
            request, form=form, adapters={}, ignore_request=False)
        widget = widgets[raw_fname]
        error = None
        try:
            widget.getInputValue()
        except:
            pass
        error = widget.error()

        res['errmsg'] = error or ''
        self.request.response.setHeader('Content-Type', 'application/json')
        return json.dumps(res)

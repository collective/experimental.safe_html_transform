from zope.browser.interfaces import ITerms
from zope.component import getMultiAdapter
from zope.schema.interfaces import ValidationError

from zope.formlib.interfaces import WidgetInputError
from zope.formlib.interfaces import ISourceQueryView
from zope.formlib.interfaces import IWidgetInputErrorView
from zope.formlib.widget import SimpleInputWidget

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


class UberSelectionWidget(SimpleInputWidget):
    _error = None

    template = ViewPageTemplateFile('uberselectionwidget.pt')
    limit_results = 20

    def __init__(self, field, request):
        SimpleInputWidget.__init__(self, field, request)
        self.source = field.source
        self.terms = getMultiAdapter((self.source, self.request), ITerms)
        self.queryview = getMultiAdapter((self.source, self.request), ISourceQueryView)

    def _value(self):
        if self._renderedValueSet():
            value = self._data
        else:
            token = self.request.form.get(self.name)

            if token is not None and token != '':
                if not isinstance(token, basestring):
                    token = token[-1]
                try:
                    value = self.terms.getValue(str(token))
                except LookupError:
                    value = self.context.missing_value
            else:
                value = self.context.missing_value

        return value

    def _getRenderValue(self):
        value = self._value()
        if value is not None:
            value = self.terms.getTerm(value)
        return value

    def hidden(self):
        value = self._value()
        if value == self.context.missing_value:
            return '' # Nothing to hide ;)

        try:
            term = self.terms.getTerm(value)
        except LookupError:
            # A value was set, but it's not valid.  Treat
            # it as if it was missing and return nothing.
            return ''

        return '<input type="hidden" name="%s" value="%s" />' % (self.name, term.token)

    def error(self):
        if self._error:
            return getMultiAdapter((self._error, self.request),
                                   IWidgetInputErrorView).snippet()
        return ""

    def __call__(self):
        value = self._getRenderValue()
        field = self.context
        results = []
        results_truncated = False
        limit = self.limit_results
        qresults = self.queryview.results(self.name)
        if qresults is not None:
            for index, item in enumerate(qresults):
                if (limit > 0 and index >= limit):
                    results_truncated = True
                    break
                results.append(self.terms.getTerm(item))
        return self.template(field=field,
                             results=results,
                             results_truncated=results_truncated,
                             name=self.name,
                             value=value)

    def getInputValue(self):
        value = self._value()

        field = self.context

        # Remaining code copied from SimpleInputWidget

        # value must be valid per the field constraints
        try:
            field.validate(value)
        except ValidationError, err:
            self._error = WidgetInputError(field.__name__, self.label, err)
            raise self._error

        return value

    def hasInput(self):
        if self.name in self.request or self.name+'.displayed' in self.request:
            return True

        token = self.request.form.get(self.name)
        if token is not None:
            return True

        return False

class UberMultiSelectionWidget(UberSelectionWidget):
    template = ViewPageTemplateFile('ubermultiselectionwidget.pt')

    def __init__(self, field, request):
        SimpleInputWidget.__init__(self, field, request)
        self.source = field.value_type.source
        self.terms = getMultiAdapter((self.source, self.request), ITerms)
        self.queryview = getMultiAdapter((self.source, self.request), ISourceQueryView)

    def _value(self):
        if self._renderedValueSet():
            value = self._data
        else:
            tokens = self.request.form.get(self.name)

            if tokens is not None:
                value = []
                for token in tokens:
                    try:
                        v = self.terms.getValue(str(token))
                    except LookupError:
                        pass # skip invalid values
                    else:
                        value.append(v)
                # only keep unique items
                r = []
                seen = {}
                for s in value:
                    if s not in seen:
                        r.append(s)
                        seen[s] = 1
                value = r
            else:
                if self.name+'.displayed' in self.request:
                    value = []
                else:
                    value = self.context.missing_value
        if value is None:
            value = []
        return value

    def _getRenderValue(self):
        value = self._value()
        if value is not None:
            value = [self.terms.getTerm(x) for x in value]
        return value

from plone.z3cform import layout
from Products.CMFCore.utils import getToolByName
from z3c.form import form, button, field
from z3c.formwidget.query.interfaces import IQuerySource
from zope.component import adapts
from zope.interface import Interface, implements
from zope import schema
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary

from plone.formwidget.autocomplete import AutocompleteFieldWidget
from plone.formwidget.autocomplete import AutocompleteMultiFieldWidget


class KeywordSource(object):
    implements(IQuerySource)

    def __init__(self, context):
        self.context = context
        catalog = getToolByName(context, 'portal_catalog')
        self.keywords = catalog.uniqueValuesFor('Subject')
        self.vocab = SimpleVocabulary.fromItems(
            [(x, x) for x in self.keywords])

    def __contains__(self, term):
        return self.vocab.__contains__(term)

    def __iter__(self):
        return self.vocab.__iter__()

    def __len__(self):
        return self.vocab.__len__()

    def getTerm(self, value):
        return self.vocab.getTerm(value)

    def getTermByToken(self, value):
        return self.vocab.getTermByToken(value)

    def search(self, query_string):
        q = query_string.lower()
        return [self.getTerm(kw) for kw in self.keywords if q in kw.lower()]


class KeywordSourceBinder(object):
    implements(IContextSourceBinder)

    def __call__(self, context):
        return KeywordSource(context)


class ITestForm(Interface):

    single_keyword = schema.Choice(title=u"Single",
        source=KeywordSourceBinder(), required=False)

    keywords = schema.List(title=u"Multiple", value_type=schema.Choice(
        title=u"Multiple", source=KeywordSourceBinder()), required=False)


class TestAdapter(object):
    implements(ITestForm)
    adapts(Interface)

    def __init__(self, context):
        self.context = context

    def _get_single_keyword(self):
        return self.context.Subject() and self.context.Subject()[0] or None

    def _set_single_keyword(self, value):
        print "setting", value

    single_keyword = property(_get_single_keyword, _set_single_keyword)

    def _get_keywords(self):
        return self.context.Subject()

    def _set_keywords(self, value):
        print "setting", value

    keywords = property(_get_keywords, _set_keywords)


class TestForm(form.Form):
    fields = field.Fields(ITestForm)
    fields['single_keyword'].widgetFactory = AutocompleteFieldWidget
    fields['keywords'].widgetFactory = AutocompleteMultiFieldWidget

    @button.buttonAndHandler(u'Ok')
    def handle_ok(self, action):
        data, errors = self.extractData()
        print data, errors

TestView = layout.wrap_form(TestForm)

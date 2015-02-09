Autocomplete widget
===================

plone.formwidget.autocomplete provides an autocomplete widget based on the
jQuery Autocomplete widget.

    >>> from plone.formwidget.autocomplete import AutocompleteFieldWidget
    >>> from plone.formwidget.autocomplete import AutocompleteMultiFieldWidget

First, we need a vocabulary to search. This is shamelessly stolen from
z3c.formwidget.query, which we extend.


    >>> from zope.interface import implements
    >>> from z3c.formwidget.query.interfaces import IQuerySource
    >>> from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

    >>> class ItalianCities(object):
    ...     implements(IQuerySource)
    ...
    ...     vocabulary = SimpleVocabulary((
    ...         SimpleTerm(u'Bologna', 'bologna', u'Bologna'),
    ...         SimpleTerm(u'Palermo', 'palermo', u'Palermo'),
    ...         SimpleTerm(u'Sorrento', 'sorrento', u'Sorrento'),
    ...         SimpleTerm(u'Torino', 'torino', u'Torino')))
    ...
    ...     def __init__(self, context):
    ...         self.context = context
    ...
    ...     __contains__ = vocabulary.__contains__
    ...     __iter__ = vocabulary.__iter__
    ...     getTerm = vocabulary.getTerm
    ...     getTermByToken = vocabulary.getTermByToken
    ...
    ...     def search(self, query_string):
    ...         return [v for v in self if query_string.lower() in v.value.lower()]

    >>> from zope.schema.interfaces import IContextSourceBinder

    >>> class ItalianCitiesSourceBinder(object):
    ...     implements(IContextSourceBinder)
    ...
    ...     def __call__(self, context):
    ...         return ItalianCities(context)

Then, we will set up a simple test form and context.

    >>> from zope.interface import alsoProvides
    >>> from OFS.SimpleItem import SimpleItem
    >>> from Testing.makerequest import makerequest
    >>> from zope.annotation.interfaces import IAttributeAnnotatable
    >>> from z3c.form.interfaces import IFormLayer

    >>> def make_request(path, form={}):
    ...     app = SimpleItem('')
    ...     request = makerequest(app).REQUEST
    ...     request.form.update(form)
    ...     alsoProvides(request, IFormLayer)
    ...     alsoProvides(request, IAttributeAnnotatable)
    ...     request._script = path.split('/')
    ...     request._steps = []
    ...     request._resetURLS()
    ...     return request

    >>> from zope.interface import Interface
    >>> from zope import schema
    >>> from z3c.form import form, field, button
    >>> from plone.z3cform.layout import wrap_form

    >>> class ICities(Interface):
    ...     favourite_city = schema.Choice(title=u"Favourite city",
    ...                                    source=ItalianCitiesSourceBinder())
    ...     visited_cities = schema.List(title=u"Visited cities",
    ...                                  value_type=schema.Choice(title=u"Selection",
    ...                                                           source=ItalianCitiesSourceBinder()))

    >>> from z3c.form.interfaces import IFieldsForm
    >>> from zope.interface import implements
    >>> class CitiesForm(form.Form):
    ...     implements(ICities)
    ...     fields = field.Fields(ICities)
    ...     fields['favourite_city'].widgetFactory = AutocompleteFieldWidget
    ...     fields['visited_cities'].widgetFactory = AutocompleteMultiFieldWidget
    ...
    ...     @button.buttonAndHandler(u'Apply')
    ...     def handleApply(self, action):
    ...         data, errors = self.extractData()
    ...         print "Submitted data:", data

    >>> form_view = wrap_form(CitiesForm)

    >>> from zope.component import provideAdapter
    >>> from zope.publisher.interfaces.browser import IBrowserRequest
    >>> from zope.interface import Interface

    >>> provideAdapter(adapts=(ICities, IBrowserRequest),
    ...                provides=Interface,
    ...                factory=form_view,
    ...                name=u"cities-form")

    >>> from OFS.SimpleItem import SimpleItem
    >>> class Bar(SimpleItem):
    ...     implements(ICities)
    ...
    ...     def __init__(self, id):
    ...         self.id = id
    ...         self.favourite_city = None
    ...         self.visited_cities = []
    ...     def absolute_url(self):
    ...         return 'http://foo/bar'

Let us now look up the form and attempt to render the widget.

    >>> from zope.component import getMultiAdapter
    >>> context = Bar('bar')

Simulates traversal:

    >>> request = make_request('bar/@@cities-form')
    >>> from Testing.makerequest import makerequest
    >>> context = makerequest(context)
    >>> form_view = getMultiAdapter((context, request), name=u"cities-form")
    >>> form_view.__name__ = 'cities-form'

Simulates partial rendering:

    >>> form = form_view.form_instance
    >>> form.__name__ = 'cities-form'
    >>> form.update()
    >>> print form.widgets['favourite_city'].render() # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    <script type="text/javascript">
    ... $('#form-widgets-favourite_city-widgets-query').autocomplete('http://foo/bar/@@cities-form/++widget++form.widgets.favourite_city/@@autocomplete-search', {
    ...

    >>> print form.widgets['visited_cities'].render() # doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
    <script type="text/javascript">
    ... $('#form-widgets-visited_cities-widgets-query').autocomplete('http://foo/bar/@@cities-form/++widget++form.widgets.visited_cities/@@autocomplete-search', {
    ...

Above, we can see that the rendered JavaScript is expecting to call a view
@@autocomplete-search on the widget to get search results. This may work
like this:

    >>> widget = form.widgets['favourite_city']
    >>> context.REQUEST._script = 'bar/@@cities-form/++widget++form.widgets.visited_cities/@@autocomplete-search'.split('/')
    >>> context.REQUEST._resetURLS()
    >>> query_request = make_request('bar/@@cities-form/++widget++form.widgets.visited_cities/@@autocomplete-search', {'q': 'or'})
    >>> search_view = getMultiAdapter((widget, query_request), name=u'autocomplete-search')
    >>> print search_view()
    sorrento|Sorrento
    torino|Torino

The results are a newline-delimited list of key-value pairs separated by
pipes.

Finally, let's prove that we can extract values from the request. The
JavaScript handler for the autocomplete search event will simply write out
checkbox or radio button widgets, so we can use the standard
z3c.formwidget.query extract() method.

  - If the search button from the query subform was clicked, then assume
    that we are doing an intermediate request for a search in non-AJAX
    mode. This button is hidden when JavaScript is enabled.

    >>> search_request = make_request('bar/@@cities-form',
    ...                               {'form.widgets.visited_cities.widgets.query': 'sorrento',
    ...                                'form.widgets.visited_cities': ['torino'],
    ...                                'form.widgets.visited_cities-empty-marker': '1',
    ...                                'form.widgets.visited_cities.buttons.search': 'Search'})
    >>> form_view = getMultiAdapter((context, search_request), name=u"cities-form")
    >>> form_view.form_instance.update()
    >>> form_view.form_instance.widgets['visited_cities'].extract() == ['torino'] # [u'torino'] in Zope 2.12
    True

  - Otherwise, if the widget id and form submit button are in the request,
    the user must have selected a radio button (single select) or one or more
    checkboxes (multi-select).

    >>> search_request = make_request('bar/@@cities-form',
    ...                               {'form.widgets.visited_cities.widgets.query': 'sorrento',
    ...                                'form.widgets.visited_cities': ['torino'],
    ...                                'form.widgets.visited_cities-empty-marker': '1',
    ...                                'form.buttons.apply': 'Apply'})
    >>> form_view = getMultiAdapter((context, search_request), name=u"cities-form")
    >>> form_view.form_instance.update()
    Submitted data: {'visited_cities': [u'Torino']}
    >>> form_view.form_instance.widgets['visited_cities'].extract() == ['torino'] # [u'torino'] in Zope 2.12
    True

  - Finally, if there nothing was selected, we return an empty list

    >>> search_request = make_request('bar/@@cities-form',
    ...                               {'form.widgets.visited_cities-empty-marker': '1',
    ...                                'form.buttons.apply': 'Apply'})
    >>> form_view = getMultiAdapter((context, search_request), name=u"cities-form")
    >>> form_view.form_instance.update()
    Submitted data: {'visited_cities': []}
    >>> form_view.form_instance.widgets['visited_cities'].extract()
    []

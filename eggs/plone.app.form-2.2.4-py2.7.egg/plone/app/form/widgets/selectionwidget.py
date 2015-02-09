from zope.formlib.itemswidgets import DropdownWidget
from zope.component import queryMultiAdapter


class LanguageDropdownChoiceWidget(DropdownWidget):
    """ A DropdownWidget which renders a localized language selection.
    """

    def __init__(self, field, request):
        """Initialize the widget."""
        super(LanguageDropdownChoiceWidget, self).__init__(field,
            field.vocabulary, request)

    def renderItemsWithValues(self, values):
        """Render the list of possible values, with those found in
        `values` being marked as selected."""

        # Sort languages by their title
        portal_state = queryMultiAdapter((self.context, self.request),
                                         name=u'plone_portal_state')
        languages = portal_state.locale().displayNames.languages

        terms = []
        languages = languages
        for term in self.vocabulary:
            value = term.value
            title = languages.get(value, term.title)
            if title == value:
                title = term.title
            terms.append((title, term.token))

        terms.sort()

        cssClass = self.cssClass
        name = self.name
        renderSelectedItem = self.renderSelectedItem
        renderItem = self.renderItem
        rendered_items = []
        count = 0

        for title, token in terms:
            if token in values:
                render = renderSelectedItem
            else:
                render = renderItem

            rendered_item = render(count, title, token, name, cssClass)
            rendered_items.append(rendered_item)
            count += 1

        return rendered_items

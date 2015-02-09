from zope.interface import Interface
import zope.schema


class IBatch(Interface):
    """A batch splits up a large number of items over multiple pages"""

    size = zope.schema.Int(title=u"The amount of items in the batch")

    firstpage = zope.schema.Int(
        title=u"The number of the first page (always 1)")

    lastpage = zope.schema.Int(title=u"The number of the last page")

    items_not_on_page = zope.schema.List(
        title=u"All items that are in the batch but not on the current page")

    multiple_pages = zope.schema.Bool(
        title=u"Boolean indicating wheter there are multiple pages or not")

    has_next = zope.schema.Bool(
        title=u"Indicator for wheter there is a page after the current one")

    has_previous = zope.schema.Bool(
        title=u"Indicator for wheter there is a page after the current one")

    previouspage = zope.schema.Int(title=u"The number of the previous page")

    nextpage = zope.schema.Int(title=u"The number of the nextpage page")

    next_item_count = zope.schema.Int(
        title=u"The number of items on the next page")

    navlist = zope.schema.List(
        title=u"List of page numbers to be used as a navigation list")

    show_link_to_first = zope.schema.Bool(
        title=u"First page not in the navigation list")

    show_link_to_last = zope.schema.Bool(
        title=u"Last page not in the navigation list")

    second_page_not_in_navlist = zope.schema.Bool(
        title=u"Second page not in the navigation list")

    before_last_page_not_in_navlist = zope.schema.Bool(
        title=u"Before last page not in the navigation list")

    islastpage = zope.schema.Bool(
        title=u"Boolean indicating wheter the current page is the last page")

    previous_pages = zope.schema.List(
        title=u"All previous pages that are in the navlist")

    next_pages = zope.schema.List(
        title=u"All previous pages that are in the navlist")

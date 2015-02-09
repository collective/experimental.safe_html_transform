from warnings import warn

from zope.interface import implements
from zope.component import getMultiAdapter, getUtility
from zope.container.interfaces import INameChooser

from Acquisition import aq_base, aq_inner, aq_parent
from OFS.SimpleItem import SimpleItem
from Products.Five.browser import BrowserView

from Products.statusmessages.interfaces import IStatusMessage
from plone.contentrules.engine.interfaces import IRuleStorage

from plone.app.contentrules import PloneMessageFactory as _
from plone.app.contentrules.browser.interfaces import IRuleAdding
from plone.app.contentrules.browser.interfaces import IRuleConditionAdding
from plone.app.contentrules.browser.interfaces import IRuleActionAdding


class RuleAdding(SimpleItem, BrowserView):

    implements(IRuleAdding)

    context = None
    request = None
    contentName = None

    # This is necessary so that context.absolute_url() works properly on the
    # add form, which in turn fixes the <base /> URL
    id = '+rule'

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def add(self, content):
        """Add the rule to the context
        """
        storage = getUtility(IRuleStorage)
        chooser = INameChooser(storage)
        name = chooser.chooseName(None, content)
        self._chosen_name = name
        storage[name] = content
        IStatusMessage(self.request).add(_(u"New content rule created. "
                                           u"Please add conditions and actions at the bottom of the page."),
                                         type=u'info')

    def renderAddButton(self):
        warn("The renderAddButton method is deprecated, use nameAllowed",
            DeprecationWarning, 2)

    def namesAccepted(self):
        return False

    def nameAllowed(self):
        return False

    def isSingleMenuItem(self):
        return False

    def addingInfo(self):
        return []

    def hasCustomAddView(self):
        return None

    def nextURL(self):
        return None


class RuleElementAdding(SimpleItem, BrowserView):

    context = None
    request = None
    contentName = None

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def nextURL(self):
        url = str(getMultiAdapter((aq_parent(self.context), self.request), name=u"absolute_url"))
        return url + "/@@manage-content-rules"

    def renderAddButton(self):
        warn("The renderAddButton method is deprecated, use nameAllowed",
            DeprecationWarning, 2)

    def namesAccepted(self):
        return False

    def nameAllowed(self):
        return False

    def isSingleMenuItem(self):
        return False

    def addingInfo(self):
        return []

    def hasCustomAddView(self):
        return None


class RuleConditionAdding(RuleElementAdding):

    implements(IRuleConditionAdding)

    # This is necessary so that context.absolute_url() works properly on the
    # add form, which in turn fixes the <base /> URL
    id = '+condition'

    def add(self, content):
        """Add the rule element to the context rule
        """
        rule = aq_base(aq_inner(self.context))
        rule.conditions.append(content)


class RuleActionAdding(RuleElementAdding):

    implements(IRuleActionAdding)

    # This is necessary so that context.absolute_url() works properly on the
    # add form, which in turn fixes the <base /> URL
    id = '+action'

    def add(self, content):
        """Add the rule element to the context rule
        """
        rule = aq_base(aq_inner(self.context))
        rule.actions.append(content)

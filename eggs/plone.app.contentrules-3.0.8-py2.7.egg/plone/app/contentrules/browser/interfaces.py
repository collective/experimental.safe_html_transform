from zope.browser.interfaces import IAdding
from zope.interface import Interface


class IContentRulesInfo(Interface):
    """Site-wide information about content rules
    """

    def show_rules_tab():
        """Determine whether or not the rules tab should be shown.
        """


class IContentRulesControlPanel(Interface):
    """Marker interface for rules control panel view
    """

    def globally_disabled():
        """Wether content rules are globally disabled or not"""


class IRuleAdding(IAdding):
    """Marker interface for rule add views.

    Rules' addviews should be registered for this.
    """


class IRuleElementAdding(IAdding):
    """Marker interface for rule element (actions/conditions) add views.

    Rules' addviews should be registered for this.
    """


class IRuleConditionAdding(IRuleElementAdding):
    pass


class IRuleActionAdding(IRuleElementAdding):
    pass


class IContentRulesForm(Interface):
    """Marker interface for forms that need content rules layout
    """

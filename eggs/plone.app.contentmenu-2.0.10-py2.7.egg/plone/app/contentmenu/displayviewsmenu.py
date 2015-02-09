from zope.browsermenu.menu import BrowserMenu
from zope.component import getAdapters
from zope.interface import implements

from plone.app.contentmenu.interfaces import IDisplayViewsMenu


class DisplayViewsMenu(BrowserMenu):

    implements(IDisplayViewsMenu)

    def getMenuItemByAction(self, object, request, action):
        # Normalize actions; strip view prefix
        if action.startswith('@@'):
            action = action[2:]
        if action.startswith('++view++'):
            action = action[8:]

        for name, item in getAdapters((object, request),
                                      self.getMenuItemType()):
            item_action = item.action
            # Normalize menu item action; never uses ++view++
            if item_action.startswith('@@'):
                item_action = item_action[2:]

            if item_action == action:
                return item

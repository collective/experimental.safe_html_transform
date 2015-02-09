from zope.container.contained import NameChooser
from zope.container.interfaces import INameChooser
from zope.interface import implements


ATTEMPTS = 100


class RuleNameChooser(NameChooser):
    """A name chooser for content rules.
    """

    implements(INameChooser)

    def __init__(self, context):
        self.context = context

    def chooseName(self, name, object):
        container = self.context

        if not name:
            name = object.__class__.__name__.lower()

        i = 1
        new_name = "%s-%d" % (name, i)
        while new_name in container and i <= ATTEMPTS:
            i += 1
            new_name = "%s-%d" % (name, i)

        self.checkName(new_name, object)
        return new_name

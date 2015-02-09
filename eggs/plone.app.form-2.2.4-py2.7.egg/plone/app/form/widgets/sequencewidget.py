from zope.formlib.sequencewidget import SequenceWidget as BaseWidget

class SequenceWidget(BaseWidget):
    """Plone specific widget that is going to include originalValue attribute
    within marker input element.
    
    It'll be used to enable unload form protection for Remove, Add widget
    buttons usage.
    """

    def _getPresenceMarker(self, count=0):
        # insert originalValue attribute if there is context
        orig = ''
        # Not all content objects must necessarily support the attributes
        if self.context.context is not None and hasattr(self.context.context,
           self.context.__name__):
            orig = ' originalValue="%d"' % len(self.context.get(
                self.context.context))
        return ('<input type="hidden" name="%s.count" value="%d"%s />' % (
            self.name, count, orig))


class TupleSequenceWidget(SequenceWidget):
    _type = tuple


class ListSequenceWidget(SequenceWidget):
    _type = list

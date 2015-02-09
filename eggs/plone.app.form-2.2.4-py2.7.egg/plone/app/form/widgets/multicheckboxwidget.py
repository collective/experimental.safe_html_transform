from zope.formlib.widget import renderElement
from zope.formlib.itemswidgets import MultiCheckBoxWidget as BaseWidget


class MultiCheckBoxWidget(BaseWidget):
    """Provide a list of checkboxes that provide the choice for the list,
       with a <label> for accessibility"""

    orientation = "vertical"

    _joinButtonToMessageTemplate = u"%s %s"
    
    def renderItem(self, index, text, value, name, cssClass):
        id = '%s.%s' % (name, index)
        elem = renderElement('input',
                             type="checkbox",
                             cssClass=cssClass,
                             name=name,
                             id=id,
                             value=value)

        label = renderElement('label',
                              extra= u"for=%s" % id,
                              contents=text)

        return self._joinButtonToMessageTemplate %(elem, label)

    def renderSelectedItem(self, index, text, value, name, cssClass):
        id = '%s.%s' % (name, index)
        elem = renderElement('input',
                             type="checkbox",
                             cssClass=cssClass,
                             name=name,
                             id=id,
                             value=value,
                             checked="checked")

        label = renderElement('label',
                              extra= u"for=%s" % id,
                              contents=text)

        return self._joinButtonToMessageTemplate %(elem, label)

from zope.schema import vocabulary

import zope.interface
import zope.component
import zope.schema.interfaces

import z3c.form.term
import z3c.form.browser.checkbox
import z3c.form.interfaces

class SingleCheckBoxWidget(z3c.form.browser.checkbox.SingleCheckBoxWidget):

    def update(self):
        self.ignoreContext = True
        super(SingleCheckBoxWidget, self).update()

    def updateTerms(self):
        # The default implementation would render "selected" as a
        # lebel for the single checkbox.  We use no label instead.
        if self.terms is None:
            self.terms = z3c.form.term.Terms()
            self.terms.terms = vocabulary.SimpleVocabulary((
                vocabulary.SimpleTerm(True, 'selected', u''),
                ))
        return self.terms

    def extract(self, default=z3c.form.interfaces.NOVALUE, setErrors=True):
        # The default implementation returns [] here.
        if (self.name not in self.request and
            self.name+'-empty-marker' in self.request):
            return default
        else:
            try:
                return super(SingleCheckBoxWidget, self).extract(default, setErrors=setErrors)
            except TypeError:
                # for z3c.form <= 1.9.0
                return super(SingleCheckBoxWidget, self).extract(default)

@zope.component.adapter(zope.schema.interfaces.IBool, z3c.form.interfaces.IFormLayer)
@zope.interface.implementer(z3c.form.interfaces.IFieldWidget)
def SingleCheckBoxFieldWidget(field, request):
    return z3c.form.widget.FieldWidget(field, SingleCheckBoxWidget(request))

# BBB:
singlecheckboxwidget_factory = SingleCheckBoxFieldWidget

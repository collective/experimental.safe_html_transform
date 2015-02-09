from zope.interface import Interface

from plone.z3cform import layout
from z3c.form import form, field
from z3c.relationfield.schema import RelationChoice, RelationList

from plone.formwidget.autocomplete.widget import (
    AutocompleteMultiFieldWidget,
    )
from plone.formwidget.contenttree import (
    ContentTreeFieldWidget,
    ObjPathSourceBinder,
    )


class ITestForm(Interface):
    multiple = RelationList(title=u"Multiple (Relations field)",
                           required=False,
                           value_type=RelationChoice(title=u"Multiple",
                     vocabulary="plone.formwidget.relations.cmfcontentsearch"))
    single = RelationChoice(title=u"Single",
                       required=False,
                       source=ObjPathSourceBinder())


class TestForm(form.EditForm):
    fields = field.Fields(ITestForm)
    fields['multiple'].widgetFactory = AutocompleteMultiFieldWidget
    fields['single'].widgetFactory = ContentTreeFieldWidget


TestView = layout.wrap_form(TestForm)

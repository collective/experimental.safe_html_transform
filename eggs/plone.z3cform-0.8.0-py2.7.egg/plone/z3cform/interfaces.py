from zope.interface import Interface, Attribute
from zope import schema

from zope.pagetemplate.interfaces import IPageTemplate
from z3c.form.interfaces import IForm

class IFormWrapper(Interface):
    """Form wrapper class.

    This class allows "two-step" rendering, with an outer view rendering
    part of the page and the form class rendering the form area.

    In Zope < 2.12, this is the only way to get z3c.form support, because
    the view class takes care of the acquisition requirement.

    In Zope 2.12 and later, this approach is optional: you may register the
    form class directly as a browser view.
    """

    def update():
        """We use the content provider update/render couple.
        """

    def render():
        """We use the content provider update/render couple.
        """

    form = Attribute("The form class. Should be set at class level")

    form_instance = schema.Object(
        title = u"Instance of the form being rendered",
        description = u"Set by the wrapper code during __init__()",
        readonly = True,
        schema = IForm
        )

    index = schema.Object(
        title = u"Page template instance",
        description = (u"If not set, a template will be found "
                       u"via an adapter lookup"),
        required = False,
        schema = IPageTemplate
        )

class IWrappedForm(Interface):
    """Marker interface applied to wrapped forms during rendering.

    This allows different handling of templates, for example.
    """

class IDeferSecurityCheck(Interface):
    """Marker interface applied to the request during traversal.

    This can be used by other code that wants to skip security
    checks during traversal.
    """

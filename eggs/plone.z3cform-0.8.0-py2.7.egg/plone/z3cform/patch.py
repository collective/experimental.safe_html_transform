"""A small monkey patch for z3c.form's BaseForm.update() and
GroupForm.update(). We need to call z2.processInputs() before the request is
used, because z3c.form expects them to have been converted to unicode first.
"""

from z3c.form.form import BaseForm
from z3c.form.group import GroupForm

from plone.z3cform.z2 import processInputs

_original_BaseForm_update = BaseForm.update
_original_GroupForm_update = GroupForm.update

def BaseForm_update(self):
    # This monkey patch ensures that processInputs() is called before
    # z3c.form does any work on the request. This is because z3c.form expects
    # charset negotiation to have taken place in the publisher, and will
    # complain about non-unicode strings

    processInputs(self.request)
    _original_BaseForm_update(self)

def GroupForm_update(self):
    # This monkey patch ensures that processInputs() is called before
    # z3c.form does any work on the request. This is because z3c.form expects
    # charset negotiation to have taken place in the publisher, and will
    # complain about non-unicode strings

    processInputs(self.request)
    _original_GroupForm_update(self)

def apply_patch():
    BaseForm.update = BaseForm_update
    GroupForm.update = GroupForm_update

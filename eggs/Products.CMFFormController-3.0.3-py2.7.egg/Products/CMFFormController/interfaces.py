from zope.interface import Interface

from Products.GenericSetup.PythonScripts.interfaces import IPythonScript

class IControllerPythonScript(IPythonScript):
    """
    Interface to differentiate btn regular python scripts and controller
    python scripts.
    """

class IControllerValidator(IPythonScript):
    """
    Interface to differentiate btn regular python scripts and controller
    validator scripts.
    """

class IFormControllerTool(Interface):
    """Marker interface for the portal_form_controller tool.
    """

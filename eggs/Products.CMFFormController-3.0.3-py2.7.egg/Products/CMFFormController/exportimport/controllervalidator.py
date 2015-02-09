from Products.GenericSetup.PythonScripts.exportimport \
     import PythonScriptBodyAdapter

from Products.CMFFormController.interfaces import IControllerValidator


class ControllerValidatorBodyAdapter(PythonScriptBodyAdapter):
    """
    Body im- and exporter for ControllerPythonScript.
    """
    __used_for__ = IControllerValidator

    suffix = '.vpy'

    def _exportBody(self):
        """Export the object as a file body.  Don't export FS versions.
        """
        if self.context.meta_type == 'Controller Validator':
            return PythonScriptBodyAdapter._exportBody(self)
        return None

    body = property(_exportBody, PythonScriptBodyAdapter._importBody)

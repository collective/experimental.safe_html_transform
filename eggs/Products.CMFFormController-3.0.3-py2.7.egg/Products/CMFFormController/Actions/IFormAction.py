from zope.interface import Interface

class IFormAction(Interface):

    def __call__(controller_state, REQUEST):
        """Executes the action. Returns either a new controller_state or
           something that should be handed off to the publication machinery.
        """
